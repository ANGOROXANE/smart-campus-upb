import hashlib
from dataclasses import dataclass

from fastapi import Request
from redis.asyncio import Redis


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    retry_after_seconds: int


class RateLimiter:
    def __init__(
        self,
        client: Redis | None,
        enabled: bool,
        requests: int,
        window_seconds: int,
    ) -> None:
        self._client = client
        self._enabled = enabled
        self._requests = requests
        self._window_seconds = window_seconds

    async def check(self, request: Request) -> RateLimitResult:
        if not self._enabled or self._client is None or _is_exempt_path(request.url.path):
            return RateLimitResult(True, self._requests, self._requests, 0)

        key = f"rate-limit:{_client_identifier(request)}"
        try:
            count = await self._client.incr(key)
            if count == 1:
                await self._client.expire(key, self._window_seconds)
            ttl = await self._client.ttl(key)
        except Exception:
            return RateLimitResult(True, self._requests, self._requests, 0)

        remaining = max(self._requests - count, 0)
        return RateLimitResult(
            allowed=count <= self._requests,
            limit=self._requests,
            remaining=remaining,
            retry_after_seconds=max(ttl, 0),
        )


def _client_identifier(request: Request) -> str:
    authorization = request.headers.get("authorization", "")
    if authorization.lower().startswith("bearer "):
        token_hash = hashlib.sha256(authorization.encode("utf-8")).hexdigest()
        return f"token:{token_hash}"
    host = request.client.host if request.client else "unknown"
    return f"ip:{host}"


def _is_exempt_path(path: str) -> bool:
    return (
        path.startswith("/health")
        or path == "/metrics"
        or path == "/docs"
        or path == "/openapi.json"
        or path.startswith("/redoc")
    )
