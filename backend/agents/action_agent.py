"""
Action Agent — executes tool calls (refund, rebook, update account, etc.)

In MVP mode these are stubbed; in production they call real APIs.
"""
from agents.base_agent import BaseAgent, AgentInput, AgentOutput
import re

ACTION_PATTERNS = {
    "refund":     re.compile(r"\b(refund|money back|reimburse|charge back)\b", re.I),
    "rebook":     re.compile(r"\b(reschedule|rebook|change (my )?(appointment|booking|date))\b", re.I),
    "cancel":     re.compile(r"\b(cancel (my )?(order|subscription|account|booking))\b", re.I),
    "track":      re.compile(r"\b(track|where is|status of) (my )?(order|package|shipment)\b", re.I),
}

STUB_RESPONSES = {
    "refund":  "I've initiated a refund of the full amount. You'll see it in 3–5 business days.",
    "rebook":  "I've rescheduled your appointment. You'll receive a confirmation email shortly.",
    "cancel":  "Your cancellation has been processed. Confirmation sent to your email.",
    "track":   "Your order is out for delivery and expected by end of day.",
}


class ActionAgent(BaseAgent):
    name = "action"

    async def _execute(self, inp: AgentInput) -> AgentOutput:
        detected_action = None
        for action, pattern in ACTION_PATTERNS.items():
            if pattern.search(inp.message):
                detected_action = action
                break

        if not detected_action:
            return AgentOutput(
                agent_name=self.name,
                result={"action": None, "message": None},
                confidence=1.0,
            )

        # In production: call real APIs here
        stub_message = STUB_RESPONSES[detected_action]

        return AgentOutput(
            agent_name=self.name,
            result={"action": detected_action, "message": stub_message, "stub": True},
            confidence=0.9,
        )
