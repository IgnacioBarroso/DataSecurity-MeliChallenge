from __future__ import annotations

import os
import time
from typing import Optional

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore

_memory_cache: dict[str, tuple[float, str]] = {}


def _get_redis_client(host: Optional[str], port: Optional[int], db: int):
    if host and port and redis is not None:
        try:
            return redis.StrictRedis(host=host, port=int(port), db=int(db), socket_timeout=1)
        except Exception:
            return None
    return None


def cache_get(key: str, host: Optional[str] = None, port: Optional[int] = None, db: int = 0) -> Optional[str]:
    client = _get_redis_client(host, port, db)
    if client is not None:
        try:
            v = client.get(key)
            if v is not None:
                return v.decode("utf-8", errors="ignore")
        except Exception:
            pass
    # memory fallback
    item = _memory_cache.get(key)
    if item is None:
        return None
    _, val = item
    return val


def cache_set(key: str, value: str, ttl_seconds: int = 86400, host: Optional[str] = None, port: Optional[int] = None, db: int = 0) -> None:
    client = _get_redis_client(host, port, db)
    if client is not None:
        try:
            client.setex(key, ttl_seconds, value.encode("utf-8"))
            return
        except Exception:
            pass
    # memory fallback with naive TTL tracking
    _memory_cache[key] = (time.time() + ttl_seconds, value)

