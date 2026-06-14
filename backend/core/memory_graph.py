"""
Unified Memory Graph — file-based cross-channel session store.
Persists conversation history across requests without requiring Redis.
"""
from __future__ import annotations
import json
import os
import time
from typing import Any

_MEMORY_FILE = os.path.join(os.path.dirname(__file__), '..', 'memory_store.json')


def _load() -> dict:
    try:
        if os.path.exists(_MEMORY_FILE):
            with open(_MEMORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {"sessions": {}, "customers": {}}


def _save(data: dict) -> None:
    try:
        with open(_MEMORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Memory] write error: {e}")


class MemoryGraph:

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
        data = _load()

        # Init session if new
        if session_id not in data["sessions"]:
            data["sessions"][session_id] = []

        # Append user turn
        data["sessions"][session_id].append({
            "ts":        time.time(),
            "channel":   channel,
            "role":      "user",
            "content":   message,
            "intent":    intent,
            "sentiment": sentiment,
        })

        # Append assistant turn
        data["sessions"][session_id].append({
            "ts":      time.time(),
            "channel": channel,
            "role":    "assistant",
            "content": response,
        })

        # Keep last 50 turns per session
        data["sessions"][session_id] = data["sessions"][session_id][-50:]

        # Track customer → sessions mapping
        if customer_id not in data["customers"]:
            data["customers"][customer_id] = []
        if session_id not in data["customers"][customer_id]:
            data["customers"][customer_id].append(session_id)

        _save(data)

    async def get_session_history(self, session_id: str) -> list[dict]:
        data = _load()
        return data["sessions"].get(session_id, [])

    async def get_customer_context(self, customer_id: str) -> dict[str, Any]:
        data = _load()
        session_ids = data["customers"].get(customer_id, [])

        all_turns = []
        channels_used = set()
        for sid in session_ids:
            turns = data["sessions"].get(sid, [])
            all_turns.extend(turns)
            channels_used.update(t["channel"] for t in turns if "channel" in t)

        sentiments = [t.get("sentiment") for t in all_turns if t.get("sentiment")]
        negative_ratio = sentiments.count("frustrated") / max(len(sentiments), 1)

        return {
            "total_interactions": len(all_turns),
            "channels_used":      list(channels_used),
            "churn_risk":         round(min(negative_ratio * 2, 1.0), 2),
            "recent_sessions":    session_ids[-5:],
        }
