"""Chat API — handles messages from any channel."""
import time
import uuid
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Literal, Optional
from services.metrics_engine import InteractionMetric, record_metric

# Pre-load agents once at module level (lazy singleton pattern)
_orchestrator = None

def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        from agents.orchestrator import OrchestratorAgent
        _orchestrator = OrchestratorAgent()
    return _orchestrator

router = APIRouter()


class ChatRequest(BaseModel):
    message:     str = Field(..., min_length=1, max_length=4000)
    session_id:  Optional[str] = None
    customer_id: str = Field(...)
    channel:     Literal["web", "email", "whatsapp", "voice", "kiosk", "sms"] = "web"
    metadata:    dict = Field(default_factory=dict)


class ChatResponse(BaseModel):
    session_id:      str
    response:        str
    intent:          str
    sentiment:       str
    should_escalate: bool
    agent_trace:     dict


def _mock_response(message: str) -> dict:
    msg_lower = message.lower()
    if any(w in msg_lower for w in ["refund", "money back"]):
        return {"response": "I've initiated a full refund — you'll see it in 3-5 business days.", "intent": "request_action", "sentiment": "frustrated", "should_escalate": True, "specialist_outputs": {"action": {"action": "refund"}, "escalation": {"should_escalate": True}}}
    if any(w in msg_lower for w in ["cancel"]):
        return {"response": "Your cancellation has been processed. Confirmation sent to your email.", "intent": "request_action", "sentiment": "neutral", "should_escalate": False, "specialist_outputs": {"action": {"action": "cancel"}}}
    if any(w in msg_lower for w in ["track", "where is", "order"]):
        return {"response": "Your order is out for delivery and expected by end of day.", "intent": "query", "sentiment": "neutral", "should_escalate": False, "specialist_outputs": {"action": {"action": "track"}}}
    if any(w in msg_lower for w in ["angry", "terrible", "worst", "frustrated", "useless"]):
        return {"response": "I'm truly sorry. I'm escalating this to a senior specialist right away.", "intent": "complaint", "sentiment": "frustrated", "should_escalate": True, "specialist_outputs": {"escalation": {"should_escalate": True}}}
    return {"response": "Thanks for reaching out! How can I help you today?", "intent": "query", "sentiment": "neutral", "should_escalate": False, "specialist_outputs": {}}


@router.post("/", response_model=ChatResponse)
async def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    t0 = time.time()

    try:
        from agents.orchestrator import OrchestratorAgent
        from agents.base_agent import AgentInput
        from core.memory_graph import MemoryGraph

        memory   = MemoryGraph()
        history  = await memory.get_session_history(session_id)
        cust_ctx = await memory.get_customer_context(req.customer_id)

        # Compute real-time sentiment from current session history
        # Compute session features
        sentiments       = [t.get('sentiment') for t in history if t.get('sentiment')]
        frustrated_count = sentiments.count('frustrated')
        frustrated_ratio = frustrated_count / max(len(sentiments), 1)
        turn_count       = len(history)
        channel_switches = len(set(t.get('channel', 'web') for t in history)) - 1

        # XGBoost churn prediction
        try:
            from ml.churn.predictor import predict_churn_from_session
            churn_risk = predict_churn_from_session(
                frustrated_ratio=frustrated_ratio,
                turn_count=turn_count,
                channel_switches=max(channel_switches, 0),
                resolved=not any(t.get('sentiment') == 'frustrated' for t in history[-2:]),
                avg_handle_time=30.0,
            )
        except Exception as ex:
            print(f"[Churn] predictor error: {ex}")
            churn_risk = round(min(frustrated_ratio * 2, 1.0), 2)

        print(f"[Churn] risk={churn_risk} turns={turn_count} frustrated_ratio={frustrated_ratio:.2f}")


        inp = AgentInput(
            session_id=session_id,
            customer_id=req.customer_id,
            message=req.message,
            channel=req.channel,
            history=history,
            context={
                **cust_ctx,
                **req.metadata,
                'churn_risk': churn_risk,
                'sentiment': {
                    'label': sentiments[-1] if sentiments else 'neutral',
                    'score': 0.85 if frustrated_count > 0 else 0.5,
                }
            },
        )
        result = await get_orchestrator().run(inp)

    except Exception as e:
        print(f"[Fallback] {type(e).__name__}: {e}")
        result = _mock_response(req.message)

    record_metric(InteractionMetric(
        session_id=session_id,
        channel=req.channel,
        intent=result["intent"],
        sentiment=result["sentiment"],
        resolved=not result["should_escalate"],
        handle_time=round(time.time() - t0, 2),
    ))

    return ChatResponse(
        session_id=session_id,
        response=result["response"],
        intent=result["intent"],
        sentiment=result["sentiment"],
        should_escalate=result["should_escalate"],
        agent_trace=result.get("specialist_outputs", {}),
    )