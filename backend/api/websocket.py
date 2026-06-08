"""WebSocket handler for real-time chat."""
import uuid, json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from core.memory_graph import MemoryGraph

router = APIRouter()
memory = MemoryGraph()


@router.websocket("/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    await websocket.accept()
    try:
        while True:
            data = json.loads(await websocket.receive_text())
            history = await memory.get_session_history(session_id)

            try:
                from agents.orchestrator import OrchestratorAgent
                from agents.base_agent import AgentInput
                inp = AgentInput(
                    session_id=session_id,
                    customer_id=data.get("customer_id", "anon"),
                    message=data["message"],
                    channel=data.get("channel", "web"),
                    history=history,
                )
                result = await OrchestratorAgent().run(inp)
            except Exception as e:
                print(f"[WS Fallback] {e}")
                result = {"response": "I received your message. How can I help?",
                          "intent": "query", "sentiment": "neutral", "should_escalate": False}

            await websocket.send_json({
                "type":            "message",
                "session_id":      session_id,
                "response":        result["response"],
                "intent":          result["intent"],
                "sentiment":       result["sentiment"],
                "should_escalate": result["should_escalate"],
            })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({"type": "error", "detail": str(e)})
        await websocket.close()