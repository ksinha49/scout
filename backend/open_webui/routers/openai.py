"""
Modification Log:
------------------
| Date       | Author         | MOD TAG            | Description                                                    |
|------------|----------------|--------------------|----------------------------------------------------------------|
| 2024-11-05 | AAK7S          | CWE-20             | Added code for sanitized url validation for openai             |
| 2025-02-12 | X1BA           | CWE-209            | Replaced direct exception messages with generic responses      |
|            |                |                    | in user-facing outputs.                                        |
| 2025-05-28 | AAK7S          | AMERITAS-ENH-3     | Proxy settings selective allocation for openai config only     |
|            |                |                    | allowing usage of Bedrock OpenAPI configuration.               |
| 2025-06-11 | AAK7S          | AMERITAS-ENH-3.1   | Added SSL certi for Bedrock API connection                     |
"""
import asyncio
import hashlib
import json
import logging
from pathlib import Path
from typing import Literal, Optional, overload
from urllib.parse import urlparse  # Added for secure URL parsing
import aiohttp
from aiocache import cached
import requests
import ssl  #AMERITAS-ENH-3.1

from fastapi import Depends, FastAPI, HTTPException, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from starlette.background import BackgroundTask

from open_webui.models.models import Models
from open_webui.config import (
    CACHE_DIR,
)
from open_webui.env import (
    AIOHTTP_CLIENT_TIMEOUT,
    AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST,
    ENABLE_FORWARD_USER_INFO_HEADERS,
    BYPASS_MODEL_ACCESS_CONTROL,
    BEDROCK_SERVER_CERT,  #AMERITAS-ENH-3.1
    IS_CERT_REQ,          #AMERITAS-ENH-3.1
)
from open_webui.models.users import UserModel

from open_webui.constants import ERROR_MESSAGES
from open_webui.env import ENV, SRC_LOG_LEVELS


from open_webui.utils.payload import (
    apply_model_params_to_body_openai,
    apply_model_system_prompt_to_body,
)
from open_webui.utils.misc import (
    convert_logit_bias_input_to_json,
)

from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.utils.access_control import has_access
from open_webui.exceptionutil import getErrorMsg

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["OPENAI"])


# AMERITAS-ENH-3.1 Initialize SSL context for Bedrock API if certificate verification is required
ssl_ctx = None
if IS_CERT_REQ:
    try:
        # Create a default SSL context and load the custom CA certificate
        ssl_ctx = ssl.create_default_context(cafile=BEDROCK_SERVER_CERT)
        log.info(f"Successfully loaded custom CA certificate from: {BEDROCK_SERVER_CERT}")
    except FileNotFoundError:
        log.error(f"Bedrock server certificate file not found at: {BEDROCK_SERVER_CERT}. SSL verification might fail.")
        # If the file is not found, ssl_ctx remains None, which will lead to default behavior or errors
        # You might want to raise an exception here if the certificate is absolutely mandatory.
    except ssl.SSLError as e:
        log.error(f"Error loading SSL certificate from {BEDROCK_SERVER_CERT}: {e}")
        # Handle other SSL-related errors during context creation
        ssl_ctx = None # Ensure it's None if there's an error
else:
    log.info("IS_CERT_REQ is False. SSL certificate verification will be disabled (not recommended for production).")

# AMERITAS-ENH-3 Helper to decide whether to trust environment proxies
def _use_env_proxies(url: str) -> bool:
    """Only use system HTTP(S)_PROXY for real OpenAI endpoints"""
    try:
        hostname = urlparse(url).hostname
        return hostname == "api.openai.com" or hostname == "openai.com"
    except Exception:
        return False
##########################################
#
# Utility functions
#
##########################################


async def send_get_request(url, key=None, user: UserModel = None):
    timeout = aiohttp.ClientTimeout(total=AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST)
    use_proxies = _use_env_proxies(url)    # AMERITAS-ENH-3 
    
    # AMERITAS-ENH-3.1
    # Use the pre-configured ssl_ctx if IS_CERT_REQ is True, otherwise pass False to disable verification
    # Passing False directly disables verification, which is generally not recommended for production.
    # The default context is created above, and if IS_CERT_REQ is False, connector will be initialized with ssl=False.
    connector = aiohttp.TCPConnector(ssl=ssl_ctx if IS_CERT_REQ else False)

    try:
        async with aiohttp.ClientSession(
            timeout=timeout, trust_env=use_proxies, connector=connector
        ) as session:
            async with session.get(
                url,
                headers={
                    **({"Authorization": f"Bearer {key}"} if key else {}),
                    **(
                        {
                            "X-Scout-User-Name": user.name,
                            "X-Scout-User-Id": user.id,
                            "X-Scout-User-Email": user.email,
                            "X-Scout-User-Role": user.role,
                        }
                        if ENABLE_FORWARD_USER_INFO_HEADERS and user
                        else {}
                    ),
                },
            ) as response:
                return await response.json()
    except aiohttp.ClientConnectorCertificateError as e:
        log.error(f"ClientConnectorCertificateError for {url}: {e}. This likely means the SSL certificate could not be verified. Check BEDROCK_SERVER_CERT path and content, or ensure the CA is trusted.")
        return {"error": "SSL_CERTIFICATE_VERIFY_FAILED", "message": str(e)}
    except Exception as e:
        # Handle connection error here
        log.error(f"Connection error to {url}: {e}")
        return None


async def cleanup_response(
    response: Optional[aiohttp.ClientResponse],
    session: Optional[aiohttp.ClientSession],
):
    if response:
        response.close()
    if session:
        await session.close()


def openai_o1_o3_handler(payload):
    """
    Handle o1, o3 specific parameters
    """
    if "max_tokens" in payload:
        # Remove "max_tokens" from the payload
        payload["max_completion_tokens"] = payload["max_tokens"]
        del payload["max_tokens"]

    # Fix: o1 and o3 do not support the "system" role directly.
    # For older models like "o1-mini" or "o1-preview", use role "user".
    # For newer o1/o3 models, replace "system" with "developer".
    if payload["messages"][0]["role"] == "system":
        model_lower = payload["model"].lower()
        if model_lower.startswith("o1-mini") or model_lower.startswith("o1-preview"):
            payload["messages"][0]["role"] = "user"
        else:
            payload["messages"][0]["role"] = "developer"

    return payload


##########################################
#
# API routes
#
##########################################

router = APIRouter()


@router.get("/config")
async def get_config(request: Request, user=Depends(get_admin_user)):
    return {
        "ENABLE_OPENAI_API": request.app.state.config.ENABLE_OPENAI_API,
        "OPENAI_API_BASE_URLS": request.app.state.config.OPENAI_API_BASE_URLS,
        "OPENAI_API_KEYS": request.app.state.config.OPENAI_API_KEYS,
        "OPENAI_API_CONFIGS": request.app.state.config.OPENAI_API_CONFIGS,
    }


class OpenAIConfigForm(BaseModel):
    ENABLE_OPENAI_API: Optional[bool] = None
    OPENAI_API_BASE_URLS: list[str]
    OPENAI_API_KEYS: list[str]
    OPENAI_API_CONFIGS: dict


@router.post("/config/update")
async def update_config(
    request: Request, form_data: OpenAIConfigForm, user=Depends(get_admin_user)
):
    request.app.state.config.ENABLE_OPENAI_API = form_data.ENABLE_OPENAI_API
    request.app.state.config.OPENAI_API_BASE_URLS = form_data.OPENAI_API_BASE_URLS
    request.app.state.config.OPENAI_API_KEYS = form_data.OPENAI_API_KEYS

    # Check if API KEYS length is same than API URLS length
    if len(request.app.state.config.OPENAI_API_KEYS) != len(
        request.app.state.config.OPENAI_API_BASE_URLS
    ):
        if len(request.app.state.config.OPENAI_API_KEYS) > len(
            request.app.state.config.OPENAI_API_BASE_URLS
        ):
            request.app.state.config.OPENAI_API_KEYS = (
                request.app.state.config.OPENAI_API_KEYS[
                    : len(request.app.state.config.OPENAI_API_BASE_URLS)
                ]
            )
        else:
            request.app.state.config.OPENAI_API_KEYS += [""] * (
                len(request.app.state.config.OPENAI_API_BASE_URLS)
                - len(request.app.state.config.OPENAI_API_KEYS)
            )

    request.app.state.config.OPENAI_API_CONFIGS = form_data.OPENAI_API_CONFIGS

    # Remove the API configs that are not in the API URLS
    keys = list(map(str, range(len(request.app.state.config.OPENAI_API_BASE_URLS))))
    request.app.state.config.OPENAI_API_CONFIGS = {
        key: value
        for key, value in request.app.state.config.OPENAI_API_CONFIGS.items()
        if key in keys
    }

    return {
        "ENABLE_OPENAI_API": request.app.state.config.ENABLE_OPENAI_API,
        "OPENAI_API_BASE_URLS": request.app.state.config.OPENAI_API_BASE_URLS,
        "OPENAI_API_KEYS": request.app.state.config.OPENAI_API_KEYS,
        "OPENAI_API_CONFIGS": request.app.state.config.OPENAI_API_CONFIGS,
    }


@router.post("/audio/speech")
async def speech(request: Request, user=Depends(get_verified_user)):
    idx = None
    try:
        idx = request.app.state.config.OPENAI_API_BASE_URLS.index(
            "https://api.openai.com/v1"
        )

        body = await request.body()
        name = hashlib.sha256(body).hexdigest()

        SPEECH_CACHE_DIR = CACHE_DIR / "audio" / "speech"
        SPEECH_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        file_path = SPEECH_CACHE_DIR.joinpath(f"{name}.mp3")
        file_body_path = SPEECH_CACHE_DIR.joinpath(f"{name}.json")

        # Check if the file already exists in the cache
        if file_path.is_file():
            return FileResponse(file_path)

        url = request.app.state.config.OPENAI_API_BASE_URLS[idx]

        r = None
        try:
            cert_val_for_requests = ssl_ctx if IS_CERT_REQ else False
            r = requests.post(
                url=f"{url}/audio/speech",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {request.app.state.config.OPENAI_API_KEYS[idx]}",
                    **(
                        {
                            "HTTP-Referer": "https://ai.inbison.com/",
                            "X-Title": "Scout",
                        }
                        if "openrouter.ai" in url
                        else {}
                    ),
                    **(
                        {
                            "X-Scout-User-Name": user.name,
                            "X-Scout-User-Id": user.id,
                            "X-Scout-User-Email": user.email,
                            "X-Scout-User-Role": user.role,
                        }
                        if ENABLE_FORWARD_USER_INFO_HEADERS
                        else {}
                    ),
                },
                stream=True,
                verify=cert_val_for_requests, # This is the key for requests library
            )

            r.raise_for_status()

            # Save the streaming content to a file
            with open(file_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

            with open(file_body_path, "w") as f:
                json.dump(json.loads(body.decode("utf-8")), f)

            # Return the saved file
            return FileResponse(file_path)

        except requests.exceptions.RequestException as e: # AMERITAS-ENH-3.1 Catch requests-specific exceptions
            log.exception(f"Request error in /audio/speech: {e}")

            detail = None
            if r is not None:
                try:
                    res = r.json()
                    if "error" in res:
                        detail = f"External: {res['error']}"
                except Exception:
                    detail = f"External: {e}"
            # AMERITAS-ENH-3.1
            status_code = r.status_code if r is not None else 500
            if isinstance(e, requests.exceptions.SSLError):
                # Specific handling for SSL errors
                status_code = 502 # Bad Gateway or similar for SSL issues
                detail = "Scout: SSL Certificate Verification Failed. Please check the server certificate or BEDROCK_SERVER_CERT path."

            raise HTTPException(
                status_code=status_code,  #AMERITAS-ENH-3.1
                detail=detail if detail else "Scout: Server Connection Error",
            )

    except ValueError:
        raise HTTPException(status_code=401, detail=ERROR_MESSAGES.OPENAI_NOT_FOUND)

## MOD: CWE-20 Sanatize url check
def is_valid_openai_url(url: str) -> bool:
    parsed_url = urlparse(url)
    return parsed_url.hostname and parsed_url.hostname == "api.openai.com"
## MOD: CWE-20 Modification end

async def get_all_models_responses(request: Request, user: UserModel) -> list:
    if not request.app.state.config.ENABLE_OPENAI_API:
        return []

    # Check if API KEYS length is same than API URLS length
    num_urls = len(request.app.state.config.OPENAI_API_BASE_URLS)
    num_keys = len(request.app.state.config.OPENAI_API_KEYS)

    if num_keys != num_urls:
        # if there are more keys than urls, remove the extra keys
        if num_keys > num_urls:
            new_keys = request.app.state.config.OPENAI_API_KEYS[:num_urls]
            request.app.state.config.OPENAI_API_KEYS = new_keys
        # if there are more urls than keys, add empty keys
        else:
            request.app.state.config.OPENAI_API_KEYS += [""] * (num_urls - num_keys)

    request_tasks = []
    for idx, url in enumerate(request.app.state.config.OPENAI_API_BASE_URLS):
        if (str(idx) not in request.app.state.config.OPENAI_API_CONFIGS) and (
            url not in request.app.state.config.OPENAI_API_CONFIGS  # Legacy support
        ):
            request_tasks.append(
                send_get_request(
                    f"{url}/models",
                    request.app.state.config.OPENAI_API_KEYS[idx],
                    user=user,
                )
            )
        else:
            api_config = request.app.state.config.OPENAI_API_CONFIGS.get(
                str(idx),
                request.app.state.config.OPENAI_API_CONFIGS.get(
                    url, {}
                ),  # Legacy support
            )

            enable = api_config.get("enable", True)
            model_ids = api_config.get("model_ids", [])

            if enable:
                if len(model_ids) == 0:
                    request_tasks.append(
                        send_get_request(
                            f"{url}/models",
                            request.app.state.config.OPENAI_API_KEYS[idx],
                            user=user,
                        )
                    )
                else:
                    model_list = {
                        "object": "list",
                        "data": [
                            {
                                "id": model_id,
                                "name": model_id,
                                "owned_by": "openai",
                                "openai": {"id": model_id},
                                "urlIdx": idx,
                            }
                            for model_id in model_ids
                        ],
                    }

                    request_tasks.append(
                        asyncio.ensure_future(asyncio.sleep(0, model_list))
                    )
            else:
                request_tasks.append(asyncio.ensure_future(asyncio.sleep(0, None)))

    responses = await asyncio.gather(*request_tasks)

    for idx, response in enumerate(responses):
        if response:
            url = request.app.state.config.OPENAI_API_BASE_URLS[idx]
            api_config = request.app.state.config.OPENAI_API_CONFIGS.get(
                str(idx),
                request.app.state.config.OPENAI_API_CONFIGS.get(
                    url, {}
                ),  # Legacy support
            )

            prefix_id = api_config.get("prefix_id", None)
            tags = api_config.get("tags", [])

            if prefix_id:
                for model in (
                    response if isinstance(response, list) else response.get("data", [])
                ):
                    model["id"] = f"{prefix_id}.{model['id']}"

            if tags:
                for model in (
                    response if isinstance(response, list) else response.get("data", [])
                ):
                    model["tags"] = tags

    log.debug(f"get_all_models:responses() {responses}")
    return responses


async def get_filtered_models(models, user):
    # Filter models based on user access control
    filtered_models = []
    for model in models.get("data", []):
        model_info = Models.get_model_by_id(model["id"])
        if model_info:
            if user.id == model_info.user_id or has_access(
                user.id, type="read", access_control=model_info.access_control
            ):
                filtered_models.append(model)
    return filtered_models


@cached(ttl=1)
async def get_all_models(request: Request, user: UserModel) -> dict[str, list]:
    log.info("get_all_models()")

    if not request.app.state.config.ENABLE_OPENAI_API:
        return {"data": []}

    responses = await get_all_models_responses(request, user=user)

    def extract_data(response):
        if response and "data" in response:
            return response["data"]
        # AMERITAS-ENH-3.1 Handle the error case from send_get_request
        if isinstance(response, dict) and "error" in response:
            log.warning(f"Skipping models from a failed connection: {response['message']}")
            return None
        if isinstance(response, list):
            return response
        return None

    def merge_models_lists(model_lists):
        log.debug(f"merge_models_lists {model_lists}")
        merged_list = []

        for idx, models in enumerate(model_lists):
            if models is not None and "error" not in models:

                merged_list.extend(
                    [
                        {
                            **model,
                            "name": model.get("name", model["id"]),
                            "owned_by": "openai",
                            "openai": model,
                            "urlIdx": idx,
                        }
                        for model in models
                        if (model.get("id") or model.get("name"))
                        and (
                            "api.openai.com"
                            not in request.app.state.config.OPENAI_API_BASE_URLS[idx]
                            or not any(
                                name in model["id"]
                                for name in [
                                    "babbage",
                                    "dall-e",
                                    "davinci",
                                    "embedding",
                                    "tts",
                                    "whisper",
                                ]
                            )
                        )
                    ]
                )

        return merged_list

    models = {"data": merge_models_lists(map(extract_data, responses))}
    log.debug(f"models: {models}")

    request.app.state.OPENAI_MODELS = {model["id"]: model for model in models["data"]}
    return models


@router.get("/models")
@router.get("/models/{url_idx}")
async def get_models(
    request: Request, url_idx: Optional[int] = None, user=Depends(get_verified_user)
):
    models = {
        "data": [],
    }

    if url_idx is None:
        models = await get_all_models(request, user=user)
    else:
        url = request.app.state.config.OPENAI_API_BASE_URLS[url_idx]
        
        ##MOD: CWE-20 Validate the URL securely using `is_valid_openai_url`
        #AMERITAS-ENH-3.1 Note: The original logic only checks for 'api.openai.com'.
        # If bedrock-api.inbison.com is a valid API endpoint, this check needs to be extended.
        if "inbison.com" not in url and not is_valid_openai_url(url): #  inbison.com is also a valid internal endpoint.
            raise HTTPException(status_code=400, detail="Invalid API URL.")
        ##MOD: CWE-20 End of Modification

        key = request.app.state.config.OPENAI_API_KEYS[url_idx]

        r = None
        # AMERITAS-ENH-3.1 Use the pre-configured ssl_ctx if IS_BEDROCK_CERT_REQ is True, otherwise pass False
        connector = aiohttp.TCPConnector(ssl=ssl_ctx if IS_CERT_REQ else False)

        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST),
            trust_env=False,
            connector=connector
        ) as session:
            try:
                async with session.get(
                    f"{url}/models",
                    headers={
                        "Authorization": f"Bearer {key}",
                        "Content-Type": "application/json",
                        **(
                            {
                                "X-Scout-User-Name": user.name,
                                "X-Scout-User-Id": user.id,
                                "X-Scout-User-Email": user.email,
                                "X-Scout-User-Role": user.role,
                            }
                            if ENABLE_FORWARD_USER_INFO_HEADERS
                            else {}
                        ),
                    },
                ) as r:
                    if r.status != 200:
                        # Extract response error details if available
                        error_detail = f"HTTP Error: {r.status}"
                        res = await r.json()
                        if "error" in res:
                            error_detail = f"External Error: {res['error']}"
                        raise Exception(error_detail)

                    response_data = await r.json()

                    # Check if we're calling OpenAI API based on the URL
            #MOD: CWE-20 Secure filtering based on validated hostname
            #if "api.openai.com" in url:
                if is_valid_openai_url(url):
                # Filter the response data
                        response_data["data"] = [
                            model
                            for model in response_data.get("data", [])
                            if not any(
                                name in model["id"]
                                for name in [
                                    "babbage",
                                    "dall-e",
                                    "davinci",
                                    "embedding",
                                    "tts",
                                    "whisper",
                                ]
                            )
                        ]

                        models = response_data
            #AMERITAS-ENH-3.1
            except aiohttp.ClientConnectorCertificateError as e:
                log.exception(f"ClientConnectorCertificateError in get_models for {url}: {str(e)}")
                raise HTTPException(
                    status_code=502, # Bad Gateway for SSL issue
                    detail="Scout: SSL Certificate Verification Failed. Please check the server certificate or BEDROCK_SERVER_CERT path."
                )
            except aiohttp.ClientError as e:
                # ClientError covers all aiohttp requests issues
                log.exception(f"Client error in get_models: {str(e)}")
                raise HTTPException(
                    status_code=500, detail="Scout: Server Connection Error"
                )
            except Exception as e:
                log.exception(f"Unexpected error in get_models: {e}")
                # MOD TAG CWE-209 Generation of Error Message Containing Sensitive Information
                error_detail = f"Unexpected error: {getErrorMsg(e)}"
                raise HTTPException(status_code=500, detail=error_detail)

    if user.role == "user" and not BYPASS_MODEL_ACCESS_CONTROL:
        models["data"] = await get_filtered_models(models, user)

    return models


class ConnectionVerificationForm(BaseModel):
    url: str
    key: str


@router.post("/verify")
async def verify_connection(
    form_data: ConnectionVerificationForm, user=Depends(get_admin_user)
):
    url = form_data.url
    key = form_data.key

    timeout = aiohttp.ClientTimeout(total=AIOHTTP_CLIENT_TIMEOUT_MODEL_LIST)
    # AMERITAS-ENH-3.1 Use the pre-configured ssl_ctx if IS_BEDROCK_CERT_REQ is True, otherwise pass False
    connector = aiohttp.TCPConnector(ssl=ssl_ctx if IS_CERT_REQ else False)
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        try:
            async with session.get(
                f"{url}/models",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                    **(
                        {
                            "X-Scout-User-Name": user.name,
                            "X-Scout-User-Id": user.id,
                            "X-Scout-User-Email": user.email,
                            "X-Scout-User-Role": user.role,
                        }
                        if ENABLE_FORWARD_USER_INFO_HEADERS
                        else {}
                    ),
                },
            ) as r:
                if r.status != 200:
                    # Extract response error details if available
                    error_detail = f"HTTP Error: {r.status}"
                    res = await r.json()
                    if "error" in res:
                        error_detail = f"External Error: {res['error']}"
                    raise Exception(error_detail)

                response_data = await r.json()
                return response_data

        #AMERITAS-ENH-3.1
        except aiohttp.ClientConnectorCertificateError as e:
            log.exception(f"ClientConnectorCertificateError in verify_connection for {url}: {str(e)}")
            raise HTTPException(
                status_code=502, # Bad Gateway for SSL issue
                detail="Scout: SSL Certificate Verification Failed. Please check the server certificate or BEDROCK_SERVER_CERT path."
            )
        except aiohttp.ClientError as e:
            # ClientError covers all aiohttp requests issues
            log.exception(f"Client error in verify_connection: {str(e)}")
            raise HTTPException(
                status_code=500, detail="Scout: Server Connection Error"
            )
        except Exception as e:
            log.exception(f"Unexpected error in verify_connection: {e}")
            # MOD TAG CWE-209 Generation of Error Message Containing Sensitive Information
            error_detail = f"Unexpected error: {getErrorMsg(e)}"
            raise HTTPException(status_code=500, detail=error_detail)


@router.post("/chat/completions")
async def generate_chat_completion(
    request: Request,
    form_data: dict,
    user=Depends(get_verified_user),
    bypass_filter: Optional[bool] = False,
):
    if BYPASS_MODEL_ACCESS_CONTROL:
        bypass_filter = True

    idx = 0

    payload = {**form_data}
    metadata = payload.pop("metadata", None)

    model_id = form_data.get("model")
    model_info = Models.get_model_by_id(model_id)

    # Check model info and override the payload
    if model_info:
        if model_info.base_model_id:
            payload["model"] = model_info.base_model_id
            model_id = model_info.base_model_id

        params = model_info.params.model_dump()
        payload = apply_model_params_to_body_openai(params, payload)
        payload = apply_model_system_prompt_to_body(params, payload, metadata, user)

        # Check if user has access to the model
        if not bypass_filter and user.role == "user":
            if not (
                user.id == model_info.user_id
                or has_access(
                    user.id, type="read", access_control=model_info.access_control
                )
            ):
                raise HTTPException(
                    status_code=403,
                    detail="Model not found",
                )
    elif not bypass_filter:
        if user.role != "admin":
            raise HTTPException(
                status_code=403,
                detail="Model not found",
            )

    await get_all_models(request, user=user)
    available_models = request.app.state.OPENAI_MODELS
    if model_id not in available_models:
        default_models = request.app.state.config.DEFAULT_MODELS
        if hasattr(default_models, "value"):
            default_models = default_models.value
        fallback_id = None
        if isinstance(default_models, list):
            fallback_id = next((m for m in default_models if m in available_models), None)
        elif isinstance(default_models, str) and default_models in available_models:
            fallback_id = default_models
        if not fallback_id and available_models:
            fallback_id = next(iter(available_models), None)
        if fallback_id:
            log.warning(
                f"Model '{model_id}' not found. Falling back to '{fallback_id}'."
            )
            model_id = fallback_id
            payload["model"] = fallback_id
        else:
            log.warning(
                f"Model '{model_id}' not found and no fallback model available."
            )
            raise HTTPException(
                status_code=404,
                detail="No valid model available",
            )
    model = available_models.get(model_id)
    idx = model["urlIdx"]

    # Get the API config for the model
    api_config = request.app.state.config.OPENAI_API_CONFIGS.get(
        str(idx),
        request.app.state.config.OPENAI_API_CONFIGS.get(
            request.app.state.config.OPENAI_API_BASE_URLS[idx], {}
        ),  # Legacy support
    )

    prefix_id = api_config.get("prefix_id", None)
    if prefix_id:
        payload["model"] = payload["model"].replace(f"{prefix_id}.", "")

    # Add user info to the payload if the model is a pipeline
    if "pipeline" in model and model.get("pipeline"):
        payload["user"] = {
            "name": user.name,
            "id": user.id,
            "email": user.email,
            "role": user.role,
        }

    url = request.app.state.config.OPENAI_API_BASE_URLS[idx]
    key = request.app.state.config.OPENAI_API_KEYS[idx]

    # Fix: o1,o3 does not support the "max_tokens" parameter, Modify "max_tokens" to "max_completion_tokens"
    is_o1_o3 = payload["model"].lower().startswith(("o1", "o3-"))
    if is_o1_o3:
        payload = openai_o1_o3_handler(payload)
    elif "api.openai.com" not in url:
        # Remove "max_completion_tokens" from the payload for backward compatibility
        if "max_completion_tokens" in payload:
            payload["max_tokens"] = payload["max_completion_tokens"]
            del payload["max_completion_tokens"]

    if "max_tokens" in payload and "max_completion_tokens" in payload:
        del payload["max_tokens"]

    # Convert the modified body back to JSON
    if "logit_bias" in payload:
        payload["logit_bias"] = json.loads(
            convert_logit_bias_input_to_json(payload["logit_bias"])
        )

    payload = json.dumps(payload)

    r = None
    session = None
    streaming = False
    response = None
    use_proxies = _use_env_proxies(url)  # AMERITAS-ENH-3 
    # Use the pre-configured ssl_ctx if IS_BEDROCK_CERT_REQ is True, otherwise pass False
    connector = aiohttp.TCPConnector(ssl=ssl_ctx if IS_CERT_REQ else False)


    try:
        session = aiohttp.ClientSession(
            trust_env=use_proxies,
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=AIOHTTP_CLIENT_TIMEOUT)
        )

        r = await session.request(
            method="POST",
            url=f"{url}/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                **(
                    {
                        "HTTP-Referer": "https://ai.inbison.com/",
                        "X-Title": "Scout",
                    }
                    if "openrouter.ai" in url
                    else {}
                ),
                **(
                    {
                        "X-Scout-User-Name": user.name,
                        "X-Scout-User-Id": user.id,
                        "X-Scout-User-Email": user.email,
                        "X-Scout-User-Role": user.role,
                    }
                    if ENABLE_FORWARD_USER_INFO_HEADERS
                    else {}
                ),
            },
        )

        # Check if response is SSE
        if "text/event-stream" in r.headers.get("Content-Type", ""):
            streaming = True
            return StreamingResponse(
                r.content,
                status_code=r.status,
                headers=dict(r.headers),
                background=BackgroundTask(
                    cleanup_response, response=r, session=session
                ),
            )
        else:
            try:
                response = await r.json()
            except Exception as e:
                log.error(e)
                response = await r.text()

            r.raise_for_status()
            return response
    #AMERITAS-ENH-3.1
    except aiohttp.ClientConnectorCertificateError as e:
        log.exception(f"ClientConnectorCertificateError in generate_chat_completion for {url}: {str(e)}")
        raise HTTPException(
            status_code=502, # Bad Gateway for SSL issue
            detail="Scout: SSL Certificate Verification Failed. Please check the server certificate or BEDROCK_SERVER_CERT path."
        )
    except Exception as e:
        log.exception(e)

        detail = None
        if isinstance(response, dict):
            if "error" in response:
                detail = f"{response['error']['message'] if 'message' in response['error'] else response['error']}"
        elif isinstance(response, str):
            detail = response

        raise HTTPException(
            status_code=r.status if r else 500,
            detail=detail if detail else "Scout: Server Connection Error",
        )
    finally:
        if not streaming and session:
            if r:
                r.close()
            await session.close()


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(path: str, request: Request, user=Depends(get_verified_user)):
    """
    Deprecated: proxy all requests to OpenAI API
    """

    body = await request.body()

    idx = 0
    url = request.app.state.config.OPENAI_API_BASE_URLS[idx]
    key = request.app.state.config.OPENAI_API_KEYS[idx]

    r = None
    session = None
    streaming = False
    use_proxies = _use_env_proxies(url)       # AMERITAS-ENH-3 
    # Use the pre-configured ssl_ctx if IS_BEDROCK_CERT_REQ is True, otherwise pass False
    connector = aiohttp.TCPConnector(ssl=ssl_ctx if IS_CERT_REQ else False)

    try:
        session = aiohttp.ClientSession(trust_env=use_proxies, connector=connector)
        r = await session.request(
            method=request.method,
            url=f"{url}/{path}",
            data=body,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                **(
                    {
                        "X-Scout-User-Name": user.name,
                        "X-Scout-User-Id": user.id,
                        "X-Scout-User-Email": user.email,
                        "X-Scout-User-Role": user.role,
                    }
                    if ENABLE_FORWARD_USER_INFO_HEADERS
                    else {}
                ),
            },
        )
        r.raise_for_status()

        # Check if response is SSE
        if "text/event-stream" in r.headers.get("Content-Type", ""):
            streaming = True
            return StreamingResponse(
                r.content,
                status_code=r.status,
                headers=dict(r.headers),
                background=BackgroundTask(
                    cleanup_response, response=r, session=session
                ),
            )
        else:
            response_data = await r.json()
            return response_data
    #AMERITAS-ENH-3.1
    except aiohttp.ClientConnectorCertificateError as e:
        log.exception(f"ClientConnectorCertificateError in proxy for {url}: {str(e)}")
        raise HTTPException(
            status_code=502, # Bad Gateway for SSL issue
            detail="Scout: SSL Certificate Verification Failed. Please check the server certificate or BEDROCK_SERVER_CERT path."
        )
    except Exception as e:
        log.exception(e)

        detail = None
        if r is not None:
            try:
                res = await r.json()
                log.error(res)
                if "error" in res:
                    detail = f"External: {res['error']['message'] if 'message' in res['error'] else res['error']}"
            except Exception:
                detail = f"External: {e}"
        raise HTTPException(
            status_code=r.status if r else 500,
            detail=detail if detail else "Scout: Server Connection Error",
        )
    finally:
        if not streaming and session:
            if r:
                r.close()
            await session.close()
