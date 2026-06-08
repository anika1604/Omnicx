"""Base class for all OmniCX specialist agents."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any
import structlog

log = structlog.get_logger()


@dataclass
class AgentInput:
    session_id: str
    customer_id: str
    message: str
    channel: str                        # web | email | whatsapp | voice | kiosk
    context: dict[str, Any] = field(default_factory=dict)
    history: list[dict] = field(default_factory=list)


@dataclass
class AgentOutput:
    agent_name: str
    result: dict[str, Any]
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Abstract base with logging and error handling."""

    name: str = "base"

    async def run(self, inp: AgentInput) -> AgentOutput:
        log.info("agent.start", agent=self.name, session=inp.session_id)
        try:
            output = await self._execute(inp)
            log.info("agent.done", agent=self.name, session=inp.session_id)
            return output
        except Exception as exc:
            log.error("agent.error", agent=self.name, error=str(exc))
            raise

    @abstractmethod
    async def _execute(self, inp: AgentInput) -> AgentOutput:
        ...
