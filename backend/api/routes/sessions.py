"""Sessions API — retrieve cross-channel customer history."""
from fastapi import APIRouter, HTTPException
from core.memory_graph import MemoryGraph

router = APIRouter()
memory = MemoryGraph()


@router.get("/{session_id}")
async def get_session(session_id: str):
    history = await memory.get_session_history(session_id)
    if not history:
        raise HTTPException(404, "Session not found")
    return {"session_id": session_id, "turns": history}


@router.get("/customer/{customer_id}/context")
async def get_customer_context(customer_id: str):
    return await memory.get_customer_context(customer_id)
