from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from services.metrics_engine import get_snapshot
import asyncio, json

router = APIRouter()

@router.get("/live")
async def live_metrics():
    return get_snapshot()

@router.get("/stream")
async def stream_metrics():
    async def event_generator():
        while True:
            data = json.dumps(get_snapshot())
            yield f"data: {data}\n\n"
            await asyncio.sleep(5)
    return StreamingResponse(event_generator(), media_type="text/event-stream")