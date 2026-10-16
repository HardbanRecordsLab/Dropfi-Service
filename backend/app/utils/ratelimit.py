"""Fixed-window rate limiting for abuse-prone endpoints (login, register,
password reset, chat, MCP).

Uses Redis when reachable (shared across API workers), otherwise an in-process
counter — same "self-working" fallback idea as the rest of the platform.
Disable with RATE_LIMIT_ENABLED=False (the test suite does).
"""
from __future__ import annotations

import logging
import threading
import time

from fastapi import HTTPException, Request

from app.config import settings

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_memory: dict[str, tuple[int, float]] = {}
_redis = None
_redis_failed_at = 0.0


def _get_redis():
    global _redis, _redis_failed_at
    if _redis is not None:
        return _redis
    if time.time() - _redis_failed_at < 60:
        return None
    try:
        import redis as redis_lib
        r = redis_lib.from_url(settings.REDIS_URL, socket_timeout=0.5, socket_connect_timeout=0.5)
        r.ping()
        _redis = r
    except Exception:  # noqa: BLE001
        _redis_failed_at = time.time()
        return None
    return _redis


def client_ip(request: Request) -> str:
    # nginx sets X-Real-IP / X-Forwarded-For in front of the API.
    fwd = request.headers.get("x-forwarded-for", "")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.headers.get("x-real-ip") or (request.client.host if request.client else "unknown")


def hit(key: str, limit: int, window_seconds: int) -> None:
    """Count one request for `key`; raise 429 once `limit` is exceeded within the window."""
    if not settings.RATE_LIMIT_ENABLED:
        return
    bucket = f"rl:{key}:{int(time.time() // window_seconds)}"
    count = None
    r = _get_redis()
    if r is not None:
        try:
            pipe = r.pipeline()
            pipe.incr(bucket)
            pipe.expire(bucket, window_seconds + 5)
            count = int(pipe.execute()[0])
        except Exception as exc:  # noqa: BLE001
            logger.warning("rate limit redis error (%s) — using in-memory counter", exc)
    if count is None:
        now = time.time()
        with _lock:
            if len(_memory) > 50_000:  # crude cleanup
                for k in [k for k, (_, exp) in _memory.items() if exp < now]:
                    _memory.pop(k, None)
            n, exp = _memory.get(bucket, (0, now + window_seconds))
            n += 1
            _memory[bucket] = (n, exp)
            count = n
    if count > limit:
        raise HTTPException(
            status_code=429,
            detail="Too many requests — please wait a moment and try again.",
            headers={"Retry-After": str(window_seconds)},
        )


def limit(name: str, max_requests: int, window_seconds: int):
    """FastAPI dependency: per-IP limit for an endpoint."""
    def dependency(request: Request) -> None:
        hit(f"{name}:{client_ip(request)}", max_requests, window_seconds)
    return dependency
