from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from open_webui.utils.auth import get_verified_user
from open_webui.exceptionutil import getErrorMsg
from open_webui.constants import ERROR_MESSAGES

from transformers import AutoModelForCausalLM, AutoTokenizer
from functools import lru_cache
import torch

router = APIRouter()

class PromptPayload(BaseModel):
    prompt: str

@router.post("/optimize")
async def optimize_prompt(request: Request, payload: PromptPayload, user=Depends(get_verified_user)):
    template = (
        "Rewrite the following text as a sequence of clear, structured steps:\n\n"
        f"{payload.prompt}"
    )
    try:
        tokenizer, model = _get_model()
        inputs = tokenizer(template, return_tensors="pt").to(model.device)
        with torch.no_grad():
            output_ids = model.generate(**inputs, max_new_tokens=256)
        optimized = tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()
        return {"optimized": optimized}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ERROR_MESSAGES.DEFAULT(getErrorMsg(e)),
        )


@lru_cache()
def _get_model():
    model_id = "mistralai/Mistral-7B-Instruct-v0.2"
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id)
    if torch.cuda.is_available():
        model = model.to("cuda")
    return tokenizer, model
