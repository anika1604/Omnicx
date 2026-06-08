"""Redis client wrapper with graceful fallback to in-memory dict."""
from __future__ import annotations
import json
from typing import Any


class _InMemoryFallback:
    """Used when Redis is not available (pure local dev)."""
    def __init__(self):
        self._store: dict[str, Any] = {}
        self._lists: dict[str, list] = {}
        self._sets:  dict[str, set]  = {}

    async def get(self, key): return self._store.get(key)
    async def set(self, key, value, ex=None): self._store[key] = value
    async def delete(self, key): self._store.pop(key, None)
    async def rpush(self, key, *values):
        self._lists.setdefault(key, []).extend(values)
    async def lrange(self, key, start, end):
        lst = self._lists.get(key, [])
        return lst[start: None if end == -1 else end + 1]
    async def expire(self, key, seconds): pass
    async def sadd(self, key, *members):
        self._sets.setdefault(key, set()).update(members)
    async def smembers(self, key): return self._sets.get(key, set())
    async def aclose(self): pass

    class _Pipeline:
        def __init__(self, store): self._store = store; self._cmds = []
        def rpush(self, *a, **kw): self._cmds.append(("rpush", a, kw)); return self
        def expire(self, *a, **kw): self._cmds.append(("expire", a, kw)); return self
        def sadd(self,  *a, **kw): self._cmds.append(("sadd",  a, kw)); return self
        async def execute(self):
            for cmd, args, kwargs in self._cmds:
                await getattr(self._store, cmd)(*args, **kwargs)

    def pipeline(self): return self._Pipeline(self)

    # async context manager support for pipeline()
    class _PipelineCM:
        def __init__(self, pipe): self._pipe = pipe
        async def __aenter__(self): return self._pipe
        async def __aexit__(self, *_): await self._pipe.execute()

    def pipeline(self):
        p = self._Pipeline(self)
        return self._PipelineCM(p)


class RedisClient:
    @staticmethod
    async def connect(url: str):
        try:
            import redis.asyncio as aioredis
            client = aioredis.from_url(url, decode_responses=True, socket_connect_timeout=2)
            await client.ping()
            print("✅ Redis connected")
            return client
        except Exception:
            print("⚠️  Redis not available — using in-memory fallback")
            return _InMemoryFallback()
