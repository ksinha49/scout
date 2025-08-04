from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
import logging

from open_webui.utils.auth import get_verified_user
from open_webui.exceptionutil import getErrorMsg
from open_webui.constants import ERROR_MESSAGES
from open_webui.utils.chat import generate_chat_completion
from open_webui.env import SRC_LOG_LEVELS

router = APIRouter()
log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MAIN"])

class PromptPayload(BaseModel):
    prompt: str

@router.post("/optimize")
async def optimize_prompt(
    request: Request, payload: PromptPayload, user=Depends(get_verified_user)
):
    if not payload.prompt or not payload.prompt.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_MESSAGES.EMPTY_CONTENT,
        )

    system_prompt = (
        "You are an expert prompt engineer. Rewrite the request below as a numbered list "
        "of concise, actionable steps, each starting with a number and a verb. "
        "Respond with only this rewritten list and no additional text."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": payload.prompt.strip()},
    ]

    try:
        response = await generate_chat_completion(
            request,
            {"model": "llama3.1:8b", "messages": messages},
            user,
            bypass_filter=True,
        )
    except HTTPException as e:
        log.exception("Upstream error during prompt optimization")
        detail = e.detail if isinstance(e.detail, str) else getErrorMsg(e)
        raise HTTPException(status_code=e.status_code, detail=detail)
    except Exception as e:
        log.exception("Failed to generate prompt optimization")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=getErrorMsg(e),
        )

    optimized = (
        response["choices"][0]["message"]["content"].strip()
        if response
        else ""
    )

    if not optimized:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Empty response from model",
        )

    return {"optimized": optimized}
