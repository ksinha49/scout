from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from open_webui.utils.auth import get_verified_user
from open_webui.exceptionutil import getErrorMsg
from open_webui.constants import ERROR_MESSAGES
from open_webui.utils.chat import generate_chat_completion

router = APIRouter()

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
        "of concise, actionable steps. Each step should begin with a number and a verb. "
        "Return only the list of steps."
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
        optimized = (
            response["choices"][0]["message"]["content"].strip()
            if response
            else ""
        )

        if not optimized:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=ERROR_MESSAGES.DEFAULT("Empty response from model"),
            )

        return {"optimized": optimized}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES.DEFAULT(getErrorMsg(e)),
        )
