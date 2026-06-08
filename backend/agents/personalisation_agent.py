"""
Personalisation Agent — recommends solutions based on customer history.
Uses simple collaborative pattern matching for MVP.
"""
from agents.base_agent import BaseAgent, AgentInput, AgentOutput

TOPIC_SOLUTIONS = {
    "refund":    ["Check refund status", "Initiate new refund", "Escalate to billing"],
    "shipping":  ["Track your order", "Contact carrier", "Request reshipment"],
    "account":   ["Reset password", "Update billing info", "Manage subscription"],
    "technical": ["View troubleshooting guide", "Clear cache & retry", "Contact tech support"],
}

class PersonalisationAgent(BaseAgent):
    name = "personalisation"

    async def _execute(self, inp: AgentInput) -> AgentOutput:
        intent  = inp.context.get("intent", "general")
        history = inp.history or []
        past_channels = list({t.get("channel") for t in history if "channel" in t})

        topic = "account"
        for key in TOPIC_SOLUTIONS:
            if key in inp.message.lower():
                topic = key
                break

        recommendations = TOPIC_SOLUTIONS.get(topic, ["Visit Help Center", "Contact Support"])

        return AgentOutput(
            agent_name=self.name,
            result={
                "recommendations": recommendations,
                "topic": topic,
                "returning_customer": len(history) > 0,
                "past_channels": past_channels,
            },
            confidence=0.8,
        )
