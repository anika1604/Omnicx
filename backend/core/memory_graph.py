"""
Unified Memory Graph — shared cross-channel session store.

Persists every interaction to Redis as a session graph so that
when a customer switches channels, full context is available instantly.
"""
from __future__ import annotations
import json
import time
from typing import Any
import redis.asyncio as aioredis
from config import get_settings

settings = get_settings()


class MemoryGraph:
    """
    Redis-backed session graph. Each session is stored as:
      omnicx:session:{session_id}  →  JSON list of interaction turns
      omnicx:customer:{customer_id} → index of session_ids across channels
    """

    def __init__(self):
        self._redis = None

    async def _get_redis(self):
        if self._redis is None:
            try:
                import redis.asyncio as aioredis
                client = aioredis.from_url(
                    settings.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=2
                )
                await client.ping()
                self._redis = client
            except Exception:
                from db.redis_client import _InMemoryFallback
                self._redis = _InMemoryFallback()
        return self._redis

    async def upsert_interaction(
        self,
        session_id: str,
        customer_id: str,
        channel: str,
        message: str,
        response: str,
        intent: str,
        sentiment: str,
    ) -> None:
        r = await self._get_redis()
        turn = {
            "ts":        time.time(),
            "channel":   channel,
            "role":      "user",
            "content":   message,
            "intent":    intent,
            "sentiment": sentiment,
        }
        assistant_turn = {
            "ts":      time.time(),
            "channel": channel,
            "role":    "assistant",
            "content": response,
        }

        session_key  = f"omnicx:session:{session_id}"
        customer_key = f"omnicx:customer:{customer_id}:sessions"

        async with r.pipeline() as pipe:
            pipe.rpush(session_key, json.dumps(turn), json.dumps(assistant_turn))
            pipe.expire(session_key, settings.redis_session_ttl)
            pipe.sadd(customer_key, session_id)
            pipe.expire(customer_key, settings.redis_session_ttl * 7)
            await pipe.execute()

    async def get_session_history(self, session_id: str) -> list[dict]:
        r = await self._get_redis()
        raw = await r.lrange(f"omnicx:session:{session_id}", 0, -1)
        return [json.loads(t) for t in raw]

    async def get_customer_context(self, customer_id: str) -> dict[str, Any]:
        """Return aggregated context across all of a customer's sessions."""
        r = await self._get_redis()
        session_ids = await r.smembers(f"omnicx:customer:{customer_id}:sessions")
        all_turns = []
        channels_used = set()
        for sid in session_ids:
            turns = await self.get_session_history(sid)
            all_turns.extend(turns)
            channels_used.update(t["channel"] for t in turns if "channel" in t)

        sentiments = [t.get("sentiment") for t in all_turns if "sentiment" in t]
        negative_ratio = sentiments.count("frustrated") / max(len(sentiments), 1)

        return {
            "total_interactions": len(all_turns),
            "channels_used":      list(channels_used),
            "churn_risk":         round(min(negative_ratio * 2, 1.0), 2),
            "recent_sessions":    list(session_ids)[-5:],
        }
