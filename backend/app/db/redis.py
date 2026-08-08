from redis.asyncio import Redis, from_url
from redis.asyncio.sentinel import Sentinel

from app.core.config import Settings


def _parse_sentinel_hosts(value: str) -> list[tuple[str, int]]:
    hosts: list[tuple[str, int]] = []
    for item in value.split(","):
        host, _, port = item.strip().partition(":")
        if not host:
            continue
        hosts.append((host, int(port or 26379)))
    return hosts


def create_redis_client(settings: Settings) -> Redis | None:
    password = (
        settings.redis_password.get_secret_value()
        if settings.redis_password is not None
        else None
    )
    if settings.redis_sentinel_hosts:
        sentinel = Sentinel(
            _parse_sentinel_hosts(settings.redis_sentinel_hosts),
            socket_timeout=settings.redis_socket_timeout_seconds,
            decode_responses=True,
            sentinel_kwargs={"password": password} if password else {},
        )
        return sentinel.master_for(
            settings.redis_sentinel_service,
            db=settings.redis_db,
            password=password,
            socket_timeout=settings.redis_socket_timeout_seconds,
            decode_responses=True,
        )

    if not settings.redis_url:
        return None
    return from_url(
        settings.redis_url,
        password=password,
        socket_timeout=settings.redis_socket_timeout_seconds,
        decode_responses=True,
    )


async def ping_redis(client: Redis | None) -> bool:
    if client is None:
        return False
    try:
        return bool(await client.ping())
    except Exception:
        return False


async def close_redis_client(client: Redis | None) -> None:
    if client is not None:
        await client.aclose()
