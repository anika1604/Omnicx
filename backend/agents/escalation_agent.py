"""
Escalation Agent — decides if the customer needs human intervention.

Triggers escalation when:
  - Sentiment is frustrated AND score >= threshold
  - Churn risk > 0.7
  - VIP customer with unresolved issue > 2 turns
  - Explicit escalation keywords detected
"""
import re
from agents.base_agent import BaseAgent, AgentInput, AgentOutput
from config import get_settings

settings = get_settings()

ESCALATION_KEYWORDS = re.compile(
    r"\b(speak to (a|the)? (human|agent|manager|supervisor|person)|"
    r"escalate|file a complaint|legal action|lawsuit|bbb)\b",
    re.IGNORECASE,
)


class EscalationAgent(BaseAgent):
    name = "escalation"

    async def _execute(self, inp: AgentInput) -> AgentOutput:
        sentiment_ctx  = inp.context.get("sentiment", {})
        churn_risk     = inp.context.get("churn_risk", 0.0)
        turn_count     = len(inp.history)
        is_vip         = inp.context.get("is_vip", False)

        reasons = []

        if (sentiment_ctx.get("label") == "frustrated"
                and sentiment_ctx.get("score", 0) >= settings.sentiment_threshold):
            reasons.append("frustrated_sentiment")

        if churn_risk > 0.7:
            reasons.append("high_churn_risk")

        if ESCALATION_KEYWORDS.search(inp.message):
            reasons.append("explicit_escalation_request")

        if is_vip and turn_count > 2:
            reasons.append("vip_unresolved")

        should_escalate = len(reasons) > 0

        return AgentOutput(
            agent_name=self.name,
            result={
                "should_escalate": should_escalate,
                "reasons": reasons,
                "churn_risk": churn_risk,
                "priority": "HIGH" if is_vip else ("MEDIUM" if should_escalate else "LOW"),
            },
            confidence=0.95,
        )
