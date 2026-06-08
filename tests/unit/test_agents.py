"""Unit tests for specialist agents."""
import pytest
import asyncio
from backend.agents.base_agent import AgentInput
from backend.agents.sentiment_agent import SentimentAgent
from backend.agents.escalation_agent import EscalationAgent
from backend.agents.action_agent import ActionAgent


def make_input(message: str, **kwargs) -> AgentInput:
    return AgentInput(
        session_id="test-session",
        customer_id="test-customer",
        message=message,
        channel="web",
        **kwargs,
    )


class TestSentimentAgent:
    @pytest.mark.asyncio
    async def test_frustrated_detection(self):
        agent = SentimentAgent()
        inp = make_input("This is the worst service I've ever experienced, I want a refund!")
        out = await agent.run(inp)
        assert out.result["label"] == "frustrated"
        assert out.result["score"] > 0.7

    @pytest.mark.asyncio
    async def test_positive_detection(self):
        agent = SentimentAgent()
        inp = make_input("This is amazing, thank you so much for your help!")
        out = await agent.run(inp)
        assert out.result["label"] == "positive"

    @pytest.mark.asyncio
    async def test_neutral_detection(self):
        agent = SentimentAgent()
        inp = make_input("What are your business hours?")
        out = await agent.run(inp)
        assert out.result["label"] == "neutral"


class TestEscalationAgent:
    @pytest.mark.asyncio
    async def test_frustrated_triggers_escalation(self):
        agent = EscalationAgent()
        inp = make_input(
            "This is unacceptable",
            context={"sentiment": {"label": "frustrated", "score": 0.91}}
        )
        out = await agent.run(inp)
        assert out.result["should_escalate"] is True
        assert "frustrated_sentiment" in out.result["reasons"]

    @pytest.mark.asyncio
    async def test_explicit_request_triggers_escalation(self):
        agent = EscalationAgent()
        inp = make_input("I want to speak to a manager")
        out = await agent.run(inp)
        assert out.result["should_escalate"] is True

    @pytest.mark.asyncio
    async def test_no_escalation_for_normal_query(self):
        agent = EscalationAgent()
        inp = make_input("What is your return policy?")
        out = await agent.run(inp)
        assert out.result["should_escalate"] is False


class TestActionAgent:
    @pytest.mark.asyncio
    async def test_refund_detection(self):
        agent = ActionAgent()
        out = await agent.run(make_input("I need a refund for my order"))
        assert out.result["action"] == "refund"

    @pytest.mark.asyncio
    async def test_no_action_for_question(self):
        agent = ActionAgent()
        out = await agent.run(make_input("What is your opening time?"))
        assert out.result["action"] is None
