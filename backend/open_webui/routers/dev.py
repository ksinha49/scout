import asyncio
from fastapi import APIRouter, HTTPException
from starlette.responses import StreamingResponse

from open_webui.env import GLOBAL_LOG_LEVEL

router = APIRouter()

@router.get("/reasoning")
async def reasoning_stream():
    if GLOBAL_LOG_LEVEL != "DEBUG":
        raise HTTPException(status_code=404, detail="Not found")

    async def event_generator():
        yield 'data: {"choices":[{"delta":{"reasoning_content":"<think>step 1"}}]}\n\n'
        await asyncio.sleep(0.01)
        yield 'data: {"choices":[{"delta":{"reasoning_content":" step 2</think>"}}]}\n\n'
        await asyncio.sleep(0.01)
        yield 'data: {"choices":[{"delta":{"content":"final answer"}}]}\n\n'
        yield 'data: [DONE]\n\n'

    return StreamingResponse(event_generator(), media_type="text/event-stream")
