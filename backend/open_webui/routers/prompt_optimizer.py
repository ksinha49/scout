from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from pathlib import Path
from functools import lru_cache

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

from open_webui.utils.auth import get_verified_user
from open_webui.exceptionutil import getErrorMsg
from open_webui.constants import ERROR_MESSAGES

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

    template = (
        "You are an expert prompt engineer. Rewrite the request below as a numbered list "
        "of concise, actionable steps. Each step should begin with a number and a verb. "
        "Return only the list of steps.\n\nRequest:\n"
        f"{payload.prompt.strip()}"
    )

    try:
        tokenizer, model = _get_model()
        inputs = tokenizer(template, return_tensors="pt").to(model.device)
        with torch.no_grad():
            output_ids = model.generate(**inputs, max_new_tokens=256)
        optimized = tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()

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


@lru_cache()
def _get_model():
    model_id = "mistralai/Mistral-7B-Instruct-v0.2"
    cache_dir = Path(__file__).resolve().parents[3] / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id, cache_dir=cache_dir)
        model = AutoModelForCausalLM.from_pretrained(model_id, cache_dir=cache_dir)
        if torch.cuda.is_available():
            model = model.to("cuda")
        return tokenizer, model
    except Exception as e:
        raise RuntimeError(f"Failed to load model '{model_id}': {e}") from e
