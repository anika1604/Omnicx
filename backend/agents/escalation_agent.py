"""
Escalation Agent — decides if the customer needs human intervention.
Also handles proactive churn intervention with retention offers.
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

RETENTION_OFFERS = [
    "As a valued customer, we'd like to offer you 20% off your next order. Use code STAY20.",
    "We appreciate your patience. Please accept a complimentary 1-month extension on your subscription.",
    "We're sorry for the inconvenience. We'd like to offer you free express shipping on your next 3 orders.",
    "As an apology for this experience, we're adding $10 credit to your account immediately.",
]


def _get_retention_offer(customer_id: str) -> str:
    """Pick a retention offer deterministically per customer."""
    idx = sum(ord(c) for c in customer_id) % len(RETENTION_OFFERS)
    return RETENTION_OFFERS[idx]


class EscalationAgent(BaseAgent):
    name = "escalation"

    async def _execute(self, inp: AgentInput) -> AgentOutput:
        sentiment_ctx = inp.context.get("sentiment", {})
        churn_risk    = inp.context.get("churn_risk", 0.0)
        turn_count    = len(inp.history)
        is_vip        = inp.context.get("is_vip", False)

        reasons = []

        # Check escalation triggers
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

        # Proactive churn intervention
        retention_offer = None
        proactive_message = None

        if churn_risk > 0.5:
            retention_offer = _get_retention_offer(inp.customer_id)
            proactive_message = (
                f"We noticed you may be having a frustrating experience and we sincerely apologize. "
                f"{retention_offer}"
            )

        # High churn — add urgent retention
        if churn_risk > 0.7:
            proactive_message = (
                f"We value you as a customer and want to make this right immediately. "
                f"{retention_offer} "
                f"A senior customer success manager will also reach out within 2 hours."
            )

        return AgentOutput(
            agent_name=self.name,
            result={
                "should_escalate":   should_escalate,
                "reasons":           reasons,
                "churn_risk":        churn_risk,
                "priority":          "HIGH" if is_vip else ("MEDIUM" if should_escalate else "LOW"),
                "retention_offer":   retention_offer,
                "proactive_message": proactive_message,
            },
            confidence=0.95,
        )