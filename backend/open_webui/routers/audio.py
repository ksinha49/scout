"""
Modification Log:
------------------
| Date       | Author         | MOD TAG            | Description                                                                                         |
|------------|----------------|--------------------|-----------------------------------------------------------------------------------------------------|
| 2024-11-05 | AAK7S          | CWE-209            | Replaced direct exception messages with generic responses in user-facing outputs.                   |
|            |                |                    | **Old Code:** Exposed detailed exception messages to users.                                         |
|            |                |                    | **New Code:** Logged exception details while providing a generic error message to users.            |
| 2025-04-06 | AAK7S          | CWE-327            | Fix for Using a broken or weak cryptographic protocol may make a connection                         |
|            |                |                    | vulnerable to interference from an attacker.                                                        |
"""

import hashlib
import json
import logging
import os
import uuid
import gzip
from functools import lru_cache
from pathlib import Path
from pydub import AudioSegment
from pydub.silence import split_on_silence

import aiohttp
import aiofiles
import requests
from requests.adapters import HTTPAdapter
import mimetypes
from urllib.parse import urlparse  # ENH CWE-327
from urllib3.util.retry import Retry
import soundfile as sf


from fastapi import (
    Depends,
    FastAPI,
    File,
    HTTPException,
    Request,
    UploadFile,
    status,
    APIRouter,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel


from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.config import (
    WHISPER_MODEL_AUTO_UPDATE,
    WHISPER_MODEL_DIR,
    CACHE_DIR,
)

from open_webui.constants import ERROR_MESSAGES
from open_webui.env import (
    AIOHTTP_CLIENT_TIMEOUT,
    ENV,
    SRC_LOG_LEVELS,
    DEVICE_TYPE,
    ENABLE_FORWARD_USER_INFO_HEADERS,
)


router = APIRouter()

# Constants
MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024  # Convert MB to bytes

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["AUDIO"])

SPEECH_CACHE_DIR = CACHE_DIR / "audio" / "speech"
SPEECH_CACHE_DIR.mkdir(parents=True, exist_ok=True)


##########################################
#
# Utility functions
#
##########################################

from pydub import AudioSegment
from pydub.utils import mediainfo


def is_mp4_audio(file_path):
    """Check if the given file is an MP4 audio file."""
    if not os.path.isfile(file_path):
        log.error(f"File not found: {file_path}")
        return False

    info = mediainfo(file_path)
    if (
        info.get("codec_name") == "aac"
        and info.get("codec_type") == "audio"
        and info.get("codec_tag_string") == "mp4a"
    ):
        return True
    return False


def convert_mp4_to_wav(file_path, output_path):
    """Convert MP4 audio file to WAV format."""
    audio = AudioSegment.from_file(file_path, format="mp4")
    audio.export(output_path, format="wav")
    log.debug(f"Converted {file_path} to {output_path}")


def set_faster_whisper_model(
    model: str, auto_update: bool = False, device: str | None = None
):
    whisper_model = None
    if model:
        force_cpu = False
        try:
            from faster_whisper import WhisperModel
        except (ImportError, OSError) as e:
            error_message = str(e).lower()
            if (
                "cuda" in error_message
                or "cudnn" in error_message
                or "libcudnn" in error_message
            ):
                log.warning(
                    "WhisperModel import failed due to missing CUDA/cuDNN libraries (%s); retrying on CPU",
                    e,
                )
                try:
                    from faster_whisper import WhisperModel
                except Exception as inner_e:
                    log.error("Retrying WhisperModel import failed: %s", inner_e)
                    return None
                force_cpu = True
            else:
                log.error("Failed to import WhisperModel: %s", e)
                return None

        faster_whisper_kwargs = {
            "model_size_or_path": model,
            "device": (
                device
                if device
                else (
                    "cpu"
                    if force_cpu
                    else (DEVICE_TYPE if DEVICE_TYPE == "cuda" else "cpu")
                )
            ),
            "compute_type": "int8",
            "download_root": WHISPER_MODEL_DIR,
            "local_files_only": not auto_update,
        }

        try:
            whisper_model = WhisperModel(**faster_whisper_kwargs)
        except RuntimeError as e:
            log.exception(
                "WhisperModel initialization failed, attempting download with local_files_only=False"
            )
            faster_whisper_kwargs["local_files_only"] = False
            try:
                whisper_model = WhisperModel(**faster_whisper_kwargs)
            except RuntimeError as e:
                log.exception("WhisperModel initialization failed")
                error_message = str(e).lower()
                if (
                    "cudnn" in error_message
                    or "libcudnn" in error_message
                    or "cuda" in error_message
                ):
                    log.warning(
                        "CUDA-related error detected (%s); falling back to CPU", e
                    )
                    faster_whisper_kwargs["device"] = "cpu"
                    try:
                        whisper_model = WhisperModel(**faster_whisper_kwargs)
                    except RuntimeError as cpu_e:
                        log.exception("Failed to initialize WhisperModel on CPU")
                        return None
                else:
                    return None
    return whisper_model


##########################################
#
# Audio API
#
##########################################


class TTSConfigForm(BaseModel):
    OPENAI_API_BASE_URL: str
    OPENAI_API_KEY: str
    API_KEY: str
    ENGINE: str
    MODEL: str
    VOICE: str
    SPLIT_ON: str
    AZURE_SPEECH_REGION: str
    AZURE_SPEECH_OUTPUT_FORMAT: str


class STTConfigForm(BaseModel):
    OPENAI_API_BASE_URL: str
    OPENAI_API_KEY: str
    ENGINE: str
    MODEL: str
    WHISPER_MODEL: str
    DEEPGRAM_API_KEY: str


class AudioConfigUpdateForm(BaseModel):
    tts: TTSConfigForm
    stt: STTConfigForm


@router.get("/config")
async def get_audio_config(request: Request, user=Depends(get_admin_user)):
    return {
        "tts": {
            "OPENAI_API_BASE_URL": request.app.state.config.TTS_OPENAI_API_BASE_URL,
            "OPENAI_API_KEY": request.app.state.config.TTS_OPENAI_API_KEY,
            "API_KEY": request.app.state.config.TTS_API_KEY,
            "ENGINE": request.app.state.config.TTS_ENGINE,
            "MODEL": request.app.state.config.TTS_MODEL,
            "VOICE": request.app.state.config.TTS_VOICE,
            "SPLIT_ON": request.app.state.config.TTS_SPLIT_ON,
            "AZURE_SPEECH_REGION": request.app.state.config.TTS_AZURE_SPEECH_REGION,
            "AZURE_SPEECH_OUTPUT_FORMAT": request.app.state.config.TTS_AZURE_SPEECH_OUTPUT_FORMAT,
        },
        "stt": {
            "OPENAI_API_BASE_URL": request.app.state.config.STT_OPENAI_API_BASE_URL,
            "OPENAI_API_KEY": request.app.state.config.STT_OPENAI_API_KEY,
            "ENGINE": request.app.state.config.STT_ENGINE,
            "MODEL": request.app.state.config.STT_MODEL,
            "WHISPER_MODEL": request.app.state.config.WHISPER_MODEL,
            "DEEPGRAM_API_KEY": request.app.state.config.DEEPGRAM_API_KEY,
        },
    }


@router.post("/config/update")
async def update_audio_config(
    request: Request, form_data: AudioConfigUpdateForm, user=Depends(get_admin_user)
):
    request.app.state.config.TTS_OPENAI_API_BASE_URL = form_data.tts.OPENAI_API_BASE_URL
    request.app.state.config.TTS_OPENAI_API_KEY = form_data.tts.OPENAI_API_KEY
    request.app.state.config.TTS_API_KEY = form_data.tts.API_KEY
    request.app.state.config.TTS_ENGINE = form_data.tts.ENGINE
    request.app.state.config.TTS_MODEL = form_data.tts.MODEL
    request.app.state.config.TTS_VOICE = form_data.tts.VOICE
    request.app.state.config.TTS_SPLIT_ON = form_data.tts.SPLIT_ON
    request.app.state.config.TTS_AZURE_SPEECH_REGION = form_data.tts.AZURE_SPEECH_REGION
    request.app.state.config.TTS_AZURE_SPEECH_OUTPUT_FORMAT = (
        form_data.tts.AZURE_SPEECH_OUTPUT_FORMAT
    )

    request.app.state.config.STT_OPENAI_API_BASE_URL = form_data.stt.OPENAI_API_BASE_URL
    request.app.state.config.STT_OPENAI_API_KEY = form_data.stt.OPENAI_API_KEY
    request.app.state.config.STT_ENGINE = form_data.stt.ENGINE
    request.app.state.config.STT_MODEL = form_data.stt.MODEL
    request.app.state.config.WHISPER_MODEL = form_data.stt.WHISPER_MODEL
    request.app.state.config.DEEPGRAM_API_KEY = form_data.stt.DEEPGRAM_API_KEY

    if request.app.state.config.STT_ENGINE == "":
        request.app.state.faster_whisper_model = set_faster_whisper_model(
            form_data.stt.WHISPER_MODEL, WHISPER_MODEL_AUTO_UPDATE
        )

    return {
        "tts": {
            "OPENAI_API_BASE_URL": request.app.state.config.TTS_OPENAI_API_BASE_URL,
            "OPENAI_API_KEY": request.app.state.config.TTS_OPENAI_API_KEY,
            "API_KEY": request.app.state.config.TTS_API_KEY,
            "ENGINE": request.app.state.config.TTS_ENGINE,
            "MODEL": request.app.state.config.TTS_MODEL,
            "VOICE": request.app.state.config.TTS_VOICE,
            "SPLIT_ON": request.app.state.config.TTS_SPLIT_ON,
            "AZURE_SPEECH_REGION": request.app.state.config.TTS_AZURE_SPEECH_REGION,
            "AZURE_SPEECH_OUTPUT_FORMAT": request.app.state.config.TTS_AZURE_SPEECH_OUTPUT_FORMAT,
        },
        "stt": {
            "OPENAI_API_BASE_URL": request.app.state.config.STT_OPENAI_API_BASE_URL,
            "OPENAI_API_KEY": request.app.state.config.STT_OPENAI_API_KEY,
            "ENGINE": request.app.state.config.STT_ENGINE,
            "MODEL": request.app.state.config.STT_MODEL,
            "WHISPER_MODEL": request.app.state.config.WHISPER_MODEL,
            "DEEPGRAM_API_KEY": request.app.state.config.DEEPGRAM_API_KEY,
        },
    }


def load_speech_pipeline(request, device: int | None = None):
    from transformers import pipeline
    from datasets import load_dataset
    from datasets.config import HF_DATASETS_CACHE

    if device is None:
        device = 0 if DEVICE_TYPE != "cpu" else -1

    # Skip reloading if dataset previously failed to load
    if getattr(request.app.state, "speech_dataset_failed", False):
        raise HTTPException(
            status_code=500,
            detail="Speech dataset failed to load previously; manual reset required",
        )

    if request.app.state.speech_synthesiser is None:
        request.app.state.speech_synthesiser = pipeline(
            "text-to-speech", "microsoft/speecht5_tts", device=device
        )

    if request.app.state.speech_speaker_embeddings_dataset is None:
        try:
            request.app.state.speech_speaker_embeddings_dataset = load_dataset(
                "Matthijs/cmu-arctic-xvectors",
                split="validation",
                download_mode="reuse_dataset_if_exists",
            )
            request.app.state.speech_dataset_failed = False
        except UnicodeDecodeError as e:
            log.warning(
                "Unicode decode error when loading dataset, attempting to decompress: %s",
                e,
            )
            try:
                cache_dir = Path(HF_DATASETS_CACHE) / "Matthijs___cmu-arctic-xvectors"
                if cache_dir.exists():
                    for gz_file in cache_dir.rglob("*.gz"):
                        with gzip.open(gz_file, "rb") as f_in:
                            with open(gz_file.with_suffix(""), "wb") as f_out:
                                f_out.write(f_in.read())
                request.app.state.speech_speaker_embeddings_dataset = load_dataset(
                    "Matthijs/cmu-arctic-xvectors",
                    split="validation",
                    download_mode="reuse_dataset_if_exists",
                )
                request.app.state.speech_dataset_failed = False
            except Exception as decompress_error:
                log.error("Failed to decompress dataset: %s", decompress_error)
                request.app.state.speech_dataset_failed = True
                raise HTTPException(
                    status_code=500,
                    detail=(
                        "Unable to load speech speaker embeddings dataset; "
                        "will not retry until reset"
                    ),
                )
        except Exception as e:
            log.exception("Unexpected error loading dataset: %s", e)
            request.app.state.speech_dataset_failed = True
            raise HTTPException(
                status_code=500,
                detail=(
                    "Unable to load speech speaker embeddings dataset; "
                    "will not retry until reset"
                ),
            )


@router.post("/speech")
async def speech(request: Request, user=Depends(get_verified_user)):
    body = await request.body()
    name = hashlib.sha256(
        body
        + str(request.app.state.config.TTS_ENGINE).encode("utf-8")
        + str(request.app.state.config.TTS_MODEL).encode("utf-8")
    ).hexdigest()

    file_path = SPEECH_CACHE_DIR.joinpath(f"{name}.mp3")
    file_body_path = SPEECH_CACHE_DIR.joinpath(f"{name}.json")

    # Check if the file already exists in the cache
    if file_path.is_file():
        return FileResponse(file_path)

    payload = None
    try:
        payload = json.loads(body.decode("utf-8"))
    except Exception as e:
        log.exception(e)
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    if request.app.state.config.TTS_ENGINE == "openai":
        payload["model"] = request.app.state.config.TTS_MODEL

        try:
            timeout = aiohttp.ClientTimeout(total=AIOHTTP_CLIENT_TIMEOUT)
            async with aiohttp.ClientSession(
                timeout=timeout, trust_env=True
            ) as session:
                async with session.post(
                    url=f"{request.app.state.config.TTS_OPENAI_API_BASE_URL}/audio/speech",
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {request.app.state.config.TTS_OPENAI_API_KEY}",
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
                    r.raise_for_status()

                    async with aiofiles.open(file_path, "wb") as f:
                        await f.write(await r.read())

                    async with aiofiles.open(file_body_path, "w") as f:
                        await f.write(json.dumps(payload))

            return FileResponse(file_path)

        except Exception as e:
            log.exception(e)
            detail = None

            try:
                if r.status != 200:
                    res = await r.json()

                    if "error" in res:
                        detail = f"External: {res['error'].get('message', '')}"
            except Exception:
                ## MOD:CWE-209
                log.exception(f"Transcribe Exception: {e}")
                detail = "External: Issue in Speech"

            raise HTTPException(
                status_code=getattr(r, "status", 500),
                detail=detail if detail else "Scout UI: Server Connection Error",
            )

    elif request.app.state.config.TTS_ENGINE == "elevenlabs":
        voice_id = payload.get("voice", "")

        if voice_id not in get_available_voices(request):
            raise HTTPException(
                status_code=400,
                detail="Invalid voice id",
            )

        try:
            timeout = aiohttp.ClientTimeout(total=AIOHTTP_CLIENT_TIMEOUT)
            async with aiohttp.ClientSession(
                timeout=timeout, trust_env=True
            ) as session:
                async with session.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                    json={
                        "text": payload["input"],
                        "model_id": request.app.state.config.TTS_MODEL,
                        "voice_settings": {"stability": 0.5, "similarity_boost": 0.5},
                    },
                    headers={
                        "Accept": "audio/mpeg",
                        "Content-Type": "application/json",
                        "xi-api-key": request.app.state.config.TTS_API_KEY,
                    },
                ) as r:
                    r.raise_for_status()

                    async with aiofiles.open(file_path, "wb") as f:
                        await f.write(await r.read())

                    async with aiofiles.open(file_body_path, "w") as f:
                        await f.write(json.dumps(payload))

            return FileResponse(file_path)

        except Exception as e:
            log.exception(e)
            detail = None

            try:
                if r.status != 200:
                    res = await r.json()
                    if "error" in res:
                        detail = f"External: {res['error'].get('message', '')}"
            except Exception:
                ## MOD:CWE-209
                log.exception(f"Transcribe Exception: {e}")
                detail = "External: Issue in Speech Processing"

            raise HTTPException(
                status_code=getattr(r, "status", 500),
                detail=detail if detail else "Scout: Server Connection Error",
            )

    elif request.app.state.config.TTS_ENGINE == "azure":
        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception as e:
            log.exception(e)
            raise HTTPException(status_code=400, detail="Invalid JSON payload")

        region = request.app.state.config.TTS_AZURE_SPEECH_REGION
        language = request.app.state.config.TTS_VOICE
        locale = "-".join(request.app.state.config.TTS_VOICE.split("-")[:1])
        output_format = request.app.state.config.TTS_AZURE_SPEECH_OUTPUT_FORMAT

        try:
            data = f"""<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="{locale}">
                <voice name="{language}">{payload["input"]}</voice>
            </speak>"""
            timeout = aiohttp.ClientTimeout(total=AIOHTTP_CLIENT_TIMEOUT)
            async with aiohttp.ClientSession(
                timeout=timeout, trust_env=True
            ) as session:
                async with session.post(
                    f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1",
                    headers={
                        "Ocp-Apim-Subscription-Key": request.app.state.config.TTS_API_KEY,
                        "Content-Type": "application/ssml+xml",
                        "X-Microsoft-OutputFormat": output_format,
                    },
                    data=data,
                ) as r:
                    r.raise_for_status()

                    async with aiofiles.open(file_path, "wb") as f:
                        await f.write(await r.read())

                    async with aiofiles.open(file_body_path, "w") as f:
                        await f.write(json.dumps(payload))

                    return FileResponse(file_path)

        except Exception as e:
            log.exception(e)
            detail = None

            try:
                if r.status != 200:
                    res = await r.json()
                    if "error" in res:
                        detail = f"External: {res['error'].get('message', '')}"
            except Exception:
                detail = f"External: {e}"

            raise HTTPException(
                status_code=getattr(r, "status", 500),
                detail=detail if detail else "Scout: Server Connection Error",
            )

    elif request.app.state.config.TTS_ENGINE == "whisperspeech":
        try:
            if getattr(request.app.state, "whisperspeech_pipe", None) is None:
                try:
                    from whisperspeech.pipeline import Pipeline
                except ModuleNotFoundError as e:
                    log.exception(e)
                    missing = getattr(e, "name", "")
                    if missing == "webdataset":
                        detail = "Install `webdataset` to use WhisperSpeech"
                    else:
                        detail = "Install WhisperSpeech to use this engine"
                    raise HTTPException(status_code=500, detail=detail)

                request.app.state.whisperspeech_pipe = Pipeline.from_pretrained(
                    s2a_ref=request.app.state.config.TTS_MODEL
                )

            pipe = request.app.state.whisperspeech_pipe
            audio = pipe.generate(payload["input"], speaker=payload.get("voice"))

            sf.write(file_path, audio, 24000)

            async with aiofiles.open(file_body_path, "w") as f:
                await f.write(json.dumps(payload))

            return FileResponse(file_path)
        except HTTPException:
            raise
        except Exception as e:
            log.exception(e)
            detail = f"External: {e}"
            raise HTTPException(
                status_code=500,
                detail=detail if detail else "Scout: Server Connection Error",
            )

    elif request.app.state.config.TTS_ENGINE == "transformers":
        payload = None
        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception as e:
            log.exception(e)
            raise HTTPException(status_code=400, detail="Invalid JSON payload")

        import torch

        load_speech_pipeline(request)

        embeddings_dataset = request.app.state.speech_speaker_embeddings_dataset

        speaker_index = 6799
        try:
            speaker_index = embeddings_dataset["filename"].index(
                request.app.state.config.TTS_MODEL
            )
        except Exception:
            pass

        speaker_embedding = torch.tensor(
            embeddings_dataset[speaker_index]["xvector"]
        ).unsqueeze(0)

        speech = request.app.state.speech_synthesiser(
            payload["input"],
            forward_params={"speaker_embeddings": speaker_embedding},
        )

        sf.write(file_path, speech["audio"], samplerate=speech["sampling_rate"])

        async with aiofiles.open(file_body_path, "w") as f:
            await f.write(json.dumps(payload))

        return FileResponse(file_path)


def transcribe(request: Request, file_path):
    log.debug(f"transcribe: {file_path}")
    filename = os.path.basename(file_path)
    file_dir = os.path.dirname(file_path)
    id = filename.split(".")[0]

    if request.app.state.config.STT_ENGINE == "":
        if request.app.state.faster_whisper_model is None:
            request.app.state.faster_whisper_model = set_faster_whisper_model(
                request.app.state.config.WHISPER_MODEL
            )

        model = request.app.state.faster_whisper_model
        try:
            segments, info = model.transcribe(file_path, beam_size=5)
        except (RuntimeError, OSError) as e:
            error_message = str(e).lower()
            if (
                "cuda" in error_message
                or "cudnn" in error_message
                or "libcudnn" in error_message
            ):
                log.warning(
                    "CUDA-related error during transcription (%s); attempting CPU fallback",
                    e,
                )
                try:
                    request.app.state.faster_whisper_model = set_faster_whisper_model(
                        request.app.state.config.WHISPER_MODEL,
                        device="cpu",
                    )
                    model = request.app.state.faster_whisper_model
                    if model is None:
                        raise RuntimeError("Failed to initialize WhisperModel on CPU")
                    segments, info = model.transcribe(file_path, beam_size=5)
                except Exception as cpu_e:
                    log.exception(cpu_e)
                    raise RuntimeError(
                        "CUDA/cuDNN libraries missing and CPU fallback failed"
                    ) from cpu_e
            else:
                log.exception(e)
                raise
        log.info(
            "Detected language '%s' with probability %f"
            % (info.language, info.language_probability)
        )

        transcript = "".join([segment.text for segment in list(segments)])
        data = {"text": transcript.strip()}

        # save the transcript to a json file
        transcript_file = f"{file_dir}/{id}.json"
        with open(transcript_file, "w") as f:
            json.dump(data, f)

        log.debug(data)
        return data
    elif request.app.state.config.STT_ENGINE == "openai":
        if is_mp4_audio(file_path):
            os.rename(file_path, file_path.replace(".wav", ".mp4"))
            # Convert MP4 audio file to WAV format
            convert_mp4_to_wav(file_path.replace(".wav", ".mp4"), file_path)

        r = None
        try:
            r = requests.post(
                url=f"{request.app.state.config.STT_OPENAI_API_BASE_URL}/audio/transcriptions",
                headers={
                    "Authorization": f"Bearer {request.app.state.config.STT_OPENAI_API_KEY}"
                },
                files={"file": (filename, open(file_path, "rb"))},
                data={"model": request.app.state.config.STT_MODEL},
            )

            r.raise_for_status()
            data = r.json()

            # save the transcript to a json file
            transcript_file = f"{file_dir}/{id}.json"
            with open(transcript_file, "w") as f:
                json.dump(data, f)

            return data
        except Exception as e:
            log.exception(e)

            detail = None
            if r is not None:
                try:
                    res = r.json()
                    if "error" in res:
                        detail = f"External: {res['error'].get('message', '')}"
                except Exception:
                    detail = f"External: {e}"

            raise Exception(detail if detail else "Scout: Server Connection Error")

    elif request.app.state.config.STT_ENGINE == "deepgram":
        try:
            # Determine the MIME type of the file
            mime, _ = mimetypes.guess_type(file_path)
            if not mime:
                mime = "audio/wav"  # fallback to wav if undetectable

            # Read the audio file
            with open(file_path, "rb") as f:
                file_data = f.read()

            # Build headers and parameters
            headers = {
                "Authorization": f"Token {request.app.state.config.DEEPGRAM_API_KEY}",
                "Content-Type": mime,
            }

            # Add model if specified
            params = {}
            if request.app.state.config.STT_MODEL:
                params["model"] = request.app.state.config.STT_MODEL

            # Make request to Deepgram API
            r = requests.post(
                "https://api.deepgram.com/v1/listen",
                headers=headers,
                params=params,
                data=file_data,
            )
            r.raise_for_status()
            response_data = r.json()

            # Extract transcript from Deepgram response
            try:
                transcript = response_data["results"]["channels"][0]["alternatives"][
                    0
                ].get("transcript", "")
            except (KeyError, IndexError) as e:
                log.error(f"Malformed response from Deepgram: {str(e)}")
                raise Exception(
                    "Failed to parse Deepgram response - unexpected response format"
                )
            data = {"text": transcript.strip()}

            # Save transcript
            transcript_file = f"{file_dir}/{id}.json"
            with open(transcript_file, "w") as f:
                json.dump(data, f)

            return data

        except Exception as e:
            log.exception(e)
            detail = None
            if r is not None:
                try:
                    res = r.json()
                    if "error" in res:
                        detail = f"External: {res['error'].get('message', '')}"
                except Exception:
                    detail = f"External: {e}"
            raise Exception(detail if detail else "Scout: Server Connection Error")


def compress_audio(file_path):
    if os.path.getsize(file_path) > MAX_FILE_SIZE:
        file_dir = os.path.dirname(file_path)
        audio = AudioSegment.from_file(file_path)
        audio = audio.set_frame_rate(16000).set_channels(1)  # Compress audio
        compressed_path = f"{file_dir}/{id}_compressed.opus"
        audio.export(compressed_path, format="opus", bitrate="32k")
        log.debug(f"Compressed audio to {compressed_path}")

        if (
            os.path.getsize(compressed_path) > MAX_FILE_SIZE
        ):  # Still larger than MAX_FILE_SIZE after compression
            raise Exception(ERROR_MESSAGES.FILE_TOO_LARGE(size=f"{MAX_FILE_SIZE_MB}MB"))
        return compressed_path
    else:
        return file_path


@router.post("/transcriptions")
def transcription(
    request: Request,
    file: UploadFile = File(...),
    user=Depends(get_verified_user),
):
    log.info(f"file.content_type: {file.content_type}")

    supported_filetypes = ("audio/mpeg", "audio/wav", "audio/ogg", "audio/x-m4a")

    if not file.content_type.startswith(supported_filetypes):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.FILE_NOT_SUPPORTED,
        )

    try:
        ext = file.filename.split(".")[-1]
        id = uuid.uuid4()

        filename = f"{id}.{ext}"
        contents = file.file.read()

        file_dir = f"{CACHE_DIR}/audio/transcriptions"
        os.makedirs(file_dir, exist_ok=True)
        file_path = f"{file_dir}/{filename}"

        with open(file_path, "wb") as f:
            f.write(contents)

        try:
            try:
                file_path = compress_audio(file_path)
            except Exception as e:
                log.exception(e)

                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ERROR_MESSAGES.DEFAULT(e),
                )

            data = transcribe(request, file_path)
            file_path = file_path.split("/")[-1]
            return {**data, "filename": file_path}
        except Exception as e:
            log.exception(e)

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ERROR_MESSAGES.DEFAULT(e),
            )

    except Exception as e:
        log.exception(e)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.DEFAULT(e),
        )


def get_available_models(request: Request) -> list[dict]:
    available_models = []
    if request.app.state.config.TTS_ENGINE == "openai":
        # Use custom endpoint if not using the official OpenAI API URL
        """ENH CWE-327
        if not request.app.state.config.TTS_OPENAI_API_BASE_URL.startswith(
            "https://api.openai.com"
        ):
        """
        parsed_url = urlparse(request.app.state.config.TTS_OPENAI_API_BASE_URL)
        if parsed_url.hostname != "api.openai.com":
            try:
                response = requests.get(
                    f"{request.app.state.config.TTS_OPENAI_API_BASE_URL}/audio/models"
                )
                response.raise_for_status()
                data = response.json()
                available_models = data.get("models", [])
            except Exception as e:
                log.error(f"Error fetching models from custom endpoint: {str(e)}")
                available_models = [{"id": "tts-1"}, {"id": "tts-1-hd"}]
        else:
            available_models = [{"id": "tts-1"}, {"id": "tts-1-hd"}]
    elif request.app.state.config.TTS_ENGINE == "elevenlabs":
        try:
            response = requests.get(
                "https://api.elevenlabs.io/v1/models",
                headers={
                    "xi-api-key": request.app.state.config.TTS_API_KEY,
                    "Content-Type": "application/json",
                },
                timeout=5,
            )
            response.raise_for_status()
            models = response.json()

            available_models = [
                {"name": model["name"], "id": model["model_id"]} for model in models
            ]
        except requests.RequestException as e:
            log.error(f"Error fetching voices: {str(e)}")
    elif request.app.state.config.TTS_ENGINE == "whisperspeech":
        available_models = [
            {"id": "collabora/whisperspeech:s2a-q4-tiny-en+pl.model"},
            {"id": "collabora/whisperspeech:s2a-q4-base-en+pl.model"},
        ]
    return available_models


@router.get("/models")
async def get_models(request: Request, user=Depends(get_verified_user)):
    return {"models": get_available_models(request)}


def get_available_voices(request) -> dict:
    """Returns {voice_id: voice_name} dict"""
    available_voices = {}
    if request.app.state.config.TTS_ENGINE == "openai":
        # Use custom endpoint if not using the official OpenAI API URL
        """ENH CWE-327
        if not request.app.state.config.TTS_OPENAI_API_BASE_URL.startswith(
            "https://api.openai.com"
        ):
        """
        parsed_url = urlparse(request.app.state.config.TTS_OPENAI_API_BASE_URL)
        if parsed_url.hostname != "api.openai.com":
            try:
                response = requests.get(
                    f"{request.app.state.config.TTS_OPENAI_API_BASE_URL}/audio/voices"
                )
                response.raise_for_status()
                data = response.json()
                voices_list = data.get("voices", [])
                available_voices = {voice["id"]: voice["name"] for voice in voices_list}
            except Exception as e:
                log.error(f"Error fetching voices from custom endpoint: {str(e)}")
                available_voices = {
                    "alloy": "alloy",
                    "echo": "echo",
                    "fable": "fable",
                    "onyx": "onyx",
                    "nova": "nova",
                    "shimmer": "shimmer",
                }
        else:
            available_voices = {
                "alloy": "alloy",
                "echo": "echo",
                "fable": "fable",
                "onyx": "onyx",
                "nova": "nova",
                "shimmer": "shimmer",
            }
    elif request.app.state.config.TTS_ENGINE == "elevenlabs":
        try:
            available_voices = get_elevenlabs_voices(
                api_key=request.app.state.config.TTS_API_KEY
            )
        except Exception:
            # Avoided @lru_cache with exception
            pass
    elif request.app.state.config.TTS_ENGINE == "whisperspeech":
        available_voices = {"default": "default"}
        try:
            ws_voices = getattr(request.app.state, "whisperspeech_voices", {})
            if isinstance(ws_voices, dict):
                available_voices.update(ws_voices)
        except Exception as e:
            log.error(f"Error fetching voices: {str(e)}")
    elif request.app.state.config.TTS_ENGINE == "azure":
        try:
            region = request.app.state.config.TTS_AZURE_SPEECH_REGION
            url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/voices/list"
            headers = {
                "Ocp-Apim-Subscription-Key": request.app.state.config.TTS_API_KEY
            }

            response = requests.get(url, headers=headers)
            response.raise_for_status()
            voices = response.json()

            for voice in voices:
                available_voices[voice["ShortName"]] = (
                    f"{voice['DisplayName']} ({voice['ShortName']})"
                )
        except requests.RequestException as e:
            log.error(f"Error fetching voices: {str(e)}")

    return available_voices


@lru_cache
def get_elevenlabs_voices(
    api_key: str,
    retries: int | None = None,
    backoff_factor: float | None = None,
) -> dict:
    """
    Note, set the following in your .env file to use Elevenlabs:
    AUDIO_TTS_ENGINE=elevenlabs
    AUDIO_TTS_API_KEY=sk_...  # Your Elevenlabs API key
    AUDIO_TTS_VOICE=EXAVITQu4vr4xnSDxMaL  # From https://api.elevenlabs.io/v1/voices
    AUDIO_TTS_MODEL=eleven_multilingual_v2
    """

    retries = (
        retries
        if retries is not None
        else int(os.getenv("ELEVENLABS_VOICES_RETRIES", 3))
    )
    backoff_factor = (
        backoff_factor
        if backoff_factor is not None
        else float(os.getenv("ELEVENLABS_VOICES_BACKOFF", 0.5))
    )

    session = requests.Session()
    retry_strategy = Retry(
        total=retries,
        connect=retries,
        read=retries,
        backoff_factor=backoff_factor,
        status_forcelist=range(500, 600),
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    try:
        response = session.get(
            "https://api.elevenlabs.io/v1/voices",
            headers={
                "xi-api-key": api_key,
                "Content-Type": "application/json",
            },
        )
        response.raise_for_status()
        voices_data = response.json()

        voices = {}
        for voice in voices_data.get("voices", []):
            voices[voice["voice_id"]] = voice["name"]
    except requests.RequestException as e:
        # Avoid @lru_cache with exception
        log.error(f"Error fetching voices after retries: {e}")
        raise RuntimeError(f"Error fetching voices: {e}") from e
    finally:
        session.close()

    return voices


@router.get("/voices")
async def get_voices(request: Request, user=Depends(get_verified_user)):
    return {
        "voices": [
            {"id": k, "name": v} for k, v in get_available_voices(request).items()
        ]
    }
