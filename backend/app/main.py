import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.ingestion import router as ingestion_router
from app.api.measurements import router as measurements_router
from app.api.metrics import router as metrics_router
from app.api.rooms import router as rooms_router
from app.api.sensors import router as sensors_router
from app.core.config import get_settings
from app.core.exceptions import DuplicateResourceError
from app.core.logging import configure_logging
from app.db.influxdb import create_influx_client
from app.db.mongodb import (
    create_mongo_client,
    ensure_mongo_indexes,
    get_mongo_database_from_client,
)
from app.db.redis import close_redis_client, create_redis_client
from app.core.security import hash_password
from app.models.user import UserRole
from app.repositories.mongo import MongoRepository
from app.services.cache import CacheService
from app.services.catalog import CatalogService
from app.services.events import EventBus
from app.services.measurements import InfluxMeasurementService
from app.services.metrics import metrics_middleware
from app.services.rate_limit import RateLimiter


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    mongo_client = create_mongo_client(settings)
    influx_client = create_influx_client(settings)
    redis_client = create_redis_client(settings)

    app.state.mongo_client = mongo_client
    app.state.mongodb = get_mongo_database_from_client(mongo_client, settings)
    try:
        await ensure_mongo_indexes(app.state.mongodb)
    except Exception:
        logger.warning("MongoDB indexes could not be ensured during startup")
    app.state.redis = redis_client
    app.state.instance_id = settings.instance_id
    mongo_repository = MongoRepository(app.state.mongodb)
    if settings.initial_admin_email and settings.initial_admin_password:
        try:
            existing_admin = await mongo_repository.get_user_by_email(
                settings.initial_admin_email
            )
            if existing_admin is None:
                await mongo_repository.create_user(
                    email=settings.initial_admin_email,
                    password_hash=hash_password(
                        settings.initial_admin_password.get_secret_value()
                    ),
                    role=UserRole.ADMIN,
                )
        except DuplicateResourceError:
            pass
        except Exception:
            logger.warning("Initial admin user could not be ensured during startup")
    app.state.cache_service = CacheService(
        client=redis_client,
        default_ttl_seconds=settings.cache_ttl_seconds,
    )
    app.state.event_bus = EventBus(
        client=redis_client,
        instance_id=settings.instance_id,
    )
    app.state.rate_limiter = RateLimiter(
        client=redis_client,
        enabled=settings.rate_limit_enabled,
        requests=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )
    app.state.catalog_service = CatalogService(
        repository=mongo_repository,
        cache=app.state.cache_service,
        event_bus=app.state.event_bus,
    )
    app.state.measurement_service = InfluxMeasurementService(
        client=influx_client,
        org=settings.influx_org,
        bucket=settings.influx_bucket,
        cache=app.state.cache_service,
        event_bus=app.state.event_bus,
        latest_cache_ttl_seconds=settings.latest_measurements_cache_ttl_seconds,
    )
    app.state.pubsub_stop_event = asyncio.Event()
    app.state.pubsub_task = asyncio.create_task(
        app.state.event_bus.listen_for_cache_invalidation(
            cache=app.state.cache_service,
            stop_event=app.state.pubsub_stop_event,
        )
    )

    try:
        yield
    finally:
        app.state.pubsub_stop_event.set()
        app.state.pubsub_task.cancel()
        try:
            await app.state.pubsub_task
        except asyncio.CancelledError:
            pass
        mongo_client.close()
        influx_client.close()
        await close_redis_client(redis_client)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)

    app = FastAPI(
        title=settings.app_name,
        description=(
            "Smart Campus UPB API. Backend foundation for campus monitoring, "
            "health checks, and future BD-GL 1 integrations."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        limiter = getattr(request.app.state, "rate_limiter", None)
        if limiter is not None:
            result = await limiter.check(request)
            if not result.allowed:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded"},
                    headers={
                        "Retry-After": str(result.retry_after_seconds),
                        "X-RateLimit-Limit": str(result.limit),
                        "X-RateLimit-Remaining": str(result.remaining),
                    },
                )
        response = await call_next(request)
        if limiter is not None:
            response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_requests)
        return response

    app.middleware("http")(metrics_middleware)

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(ingestion_router)
    app.include_router(rooms_router)
    app.include_router(sensors_router)
    app.include_router(measurements_router)
    app.include_router(metrics_router)

    logger.info("Application configured for environment %s", settings.app_env)
    return app


app = create_app()
