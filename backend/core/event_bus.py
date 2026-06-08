"""Simple in-process event bus for async metric broadcasting."""
import asyncio
from collections import defaultdict
from typing import Callable, Any


class EventBus:
    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event: str, callback: Callable) -> None:
        self._subscribers[event].append(callback)

    async def publish(self, event: str, payload: Any) -> None:
        for cb in self._subscribers.get(event, []):
            if asyncio.iscoroutinefunction(cb):
                await cb(payload)
            else:
                cb(payload)
