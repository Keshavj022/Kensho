"""Thread-safe in-process TTL cache for expensive external calls (SerpApi, Places).
Used via @cached(namespace, ttl) or get_cache().get/set."""
from __future__ import annotations

import functools
import hashlib
import json
import threading
import time
from typing import Any, Callable, Optional


class TTLCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, Optional[float]]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return None
            value, expires_at = item
            if expires_at is not None and expires_at < time.time():
                self._store.pop(key, None)
                return None
            return value

    def set(self, key: str, value: Any, ttl_seconds: Optional[float]) -> None:
        expires_at = time.time() + ttl_seconds if ttl_seconds else None
        with self._lock:
            self._store[key] = (value, expires_at)

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def __len__(self) -> int:  # pragma: no cover - introspection helper
        with self._lock:
            return len(self._store)


_CACHE = TTLCache()


def get_cache() -> TTLCache:
    return _CACHE


def make_key(namespace: str, payload: Any) -> str:
    raw = namespace + "|" + json.dumps(payload, sort_keys=True, default=str)
    return namespace + ":" + hashlib.md5(raw.encode("utf-8")).hexdigest()


def cached(namespace: str, ttl_seconds: Optional[float]) -> Callable:
    """Memoize a function's return by its (args, kwargs) for ttl_seconds.

    Only caches truthy results that are NOT graceful-error dicts (so a transient
    "not configured"/"request_failed" result is retried next call, not pinned).
    """

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            key = make_key(namespace, {"args": args, "kwargs": kwargs})
            hit = _CACHE.get(key)
            if hit is not None:
                return hit
            result = fn(*args, **kwargs)
            if _is_cacheable(result):
                _CACHE.set(key, result, ttl_seconds)
            return result

        return wrapper

    return decorator


def _is_cacheable(result: Any) -> bool:
    if result is None:
        return False
    if isinstance(result, dict) and result.get("_error"):
        return False
    if isinstance(result, dict) and result.get("status") in {"not_configured", "error"}:
        return False
    return True
