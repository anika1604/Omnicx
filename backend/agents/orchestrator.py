"""
Orchestrator Agent — the LangGraph-powered master router.
"""
from __future__ import annotations
from typing import TypedDict
import asyncio
import json
import re

from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

from agents.base_agent import AgentInput, AgentOutput
from agents.sentiment_agent import SentimentAgent
from agents.knowledge_agent import KnowledgeAgent
from agents.escalation_agent import EscalationAgent
from agents.action_agent import ActionAgent
from core.memory_graph import MemoryGraph
from config import get_settings

settings = get_settings()

SYSTEM_PROMPT = """You are the OmniCX Orchestrator — a world-class customer experience AI.

Your job:
1. Understand the customer's INTENT (from: query | complaint | request_action | feedback | churn_signal)
2. Identify which specialist agents to invoke
3. Compose a warm, helpful, channel-appropriate response using the conversation history

Always output valid JSON with no markdown:
{
  "intent": "<intent_label>",
  "sentiment_label": "<positive|neutral|negative|frustrated>",
  "agents_needed": ["knowledge"],
  "draft_response": "<your response to the customer>",
  "confidence": 0.95
}"""


class OrchestratorState(TypedDict):
    inp: AgentInput
    intent: str
    sentiment_label: str
    agents_needed: list[str]
    draft_response: str
    specialist_outputs: dict
    final_response: str
    should_escalate: bool


class OrchestratorAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            google_api_key=settings.gemini_api_key,
            transport="rest",
            temperature=0.3,
        )
        self.memory = MemoryGraph()
        self.sentiment_agent = SentimentAgent()
        self.knowledge_agent = KnowledgeAgent()
        self.escalation_agent = EscalationAgent()
        self.action_agent = ActionAgent()
        self._graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(OrchestratorState)
        graph.add_node("classify",         self._classify_node)
        graph.add_node("run_specialists",  self._specialists_node)
        graph.add_node("compose_response", self._compose_node)
        graph.add_node("write_memory",     self._memory_node)
        graph.set_entry_point("classify")
        graph.add_edge("classify",         "run_specialists")
        graph.add_edge("run_specialists",  "compose_response")
        graph.add_edge("compose_response", "write_memory")
        graph.add_edge("write_memory",     END)
        return graph.compile()

    async def _classify_node(self, state: OrchestratorState) -> OrchestratorState:
        inp = state["inp"]

        # Build conversation history string
        history_lines = []
        for turn in inp.history[-10:]:
            role = "Customer" if turn.get("role") == "user" else "Agent"
            history_lines.append(f"{role}: {turn.get('content', '')}")
        history_ctx = "\n".join(history_lines) if history_lines else "No previous conversation."

        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=(
                f"Channel: {inp.channel}\n\n"
                f"Previous conversation:\n{history_ctx}\n\n"
                f"New message from customer: {inp.message}\n\n"
                f"Use the conversation history to personalize your response. "
                f"If the customer mentioned their name, use it."
            )),
        ]

        response = await asyncio.get_event_loop().run_in_executor(
            None, self.llm.invoke, messages
        )

        try:
            raw = response.content
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            parsed = json.loads(match.group() if match else raw)
        except Exception:
            parsed = {}

        return {
            **state,
            "intent":          parsed.get("intent", "query"),
            "sentiment_label": parsed.get("sentiment_label", "neutral"),
            "agents_needed":   parsed.get("agents_needed", ["knowledge"]),
            "draft_response":  parsed.get("draft_response", ""),
        }

    async def _specialists_node(self, state: OrchestratorState) -> OrchestratorState:
        inp    = state["inp"]
        needed = state["agents_needed"]

        agent_map = {
            "sentiment":  self.sentiment_agent,
            "knowledge":  self.knowledge_agent,
            "escalation": self.escalation_agent,
            "action":     self.action_agent,
        }

        tasks = {
            name: agent_map[name].run(inp)
            for name in needed if name in agent_map
        }

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        outputs = {}
        for name, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                outputs[name] = {"error": str(result)}
            else:
                outputs[name] = result.result

        return {**state, "specialist_outputs": outputs}

    async def _compose_node(self, state: OrchestratorState) -> OrchestratorState:
        outputs = state["specialist_outputs"]
        draft   = state["draft_response"]

        # Use knowledge agent answer if available
        if "knowledge" in outputs and outputs["knowledge"].get("answer"):
            final = outputs["knowledge"]["answer"]
        else:
            final = draft if draft else "How can I help you today?"

        # Check escalation
        should_escalate = (
            "escalation" in outputs
            and outputs["escalation"].get("should_escalate", False)
        )
        if should_escalate:
            final += "\n\nI'm connecting you to a specialist who can help further."

        # Proactive churn intervention — append retention offer
        if "escalation" in outputs:
            proactive = outputs["escalation"].get("proactive_message")
            churn_risk = outputs["escalation"].get("churn_risk", 0)
            if proactive and churn_risk > 0.5:
                final += f"\n\n💙 {proactive}"

        return {**state, "final_response": final, "should_escalate": should_escalate}

    async def _memory_node(self, state: OrchestratorState) -> OrchestratorState:
        await self.memory.upsert_interaction(
            session_id=state["inp"].session_id,
            customer_id=state["inp"].customer_id,
            channel=state["inp"].channel,
            message=state["inp"].message,
            response=state["final_response"],
            intent=state["intent"],
            sentiment=state["sentiment_label"],
        )
        return state

    async def run(self, inp: AgentInput) -> dict:
        initial_state: OrchestratorState = {
            "inp":                inp,
            "intent":             "",
            "sentiment_label":    "",
            "agents_needed":      [],
            "draft_response":     "",
            "specialist_outputs": {},
            "final_response":     "",
            "should_escalate":    False,
        }
        final_state = await self._graph.ainvoke(initial_state)
        return {
            "response":           final_state["final_response"],
            "intent":             final_state["intent"],
            "sentiment":          final_state["sentiment_label"],
            "should_escalate":    final_state["should_escalate"],
            "specialist_outputs": final_state["specialist_outputs"],
        }