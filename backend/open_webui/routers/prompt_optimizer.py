from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from open_webui.utils.auth import get_verified_user
from open_webui.utils.chat import generate_chat_completion
from open_webui.exceptionutil import getErrorMsg
from open_webui.constants import ERROR_MESSAGES

router = APIRouter()

class PromptPayload(BaseModel):
    prompt: str

@router.post("/optimize")
async def optimize_prompt(request: Request, payload: PromptPayload, user=Depends(get_verified_user)):
    template = (
        "Rewrite the following text as a sequence of clear, structured steps:\n\n"
        f"{payload.prompt}"
    )
    messages = [
        {
            "role": "system",
            "content": "You rewrite prompts into clear, structured, step-by-step instructions.",
        },
        {"role": "user", "content": template},
    ]
    body = {"model": "mistral-small", "messages": messages}
    try:
        res = await generate_chat_completion(request, form_data=body, user=user)
        optimized = res["choices"][0]["message"]["content"]
        return {"optimized": optimized}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES.DEFAULT(getErrorMsg(e)),
        )
