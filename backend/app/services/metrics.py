import time

from fastapi import Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest


REQUEST_COUNT = Counter(
    "smart_campus_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQUEST_DURATION = Histogram(
    "smart_campus_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)
HTTP_ERRORS = Counter(
    "smart_campus_http_errors_total",
    "Total HTTP error responses",
    ["method", "path", "status"],
)
DEPENDENCY_STATUS = Gauge(
    "smart_campus_dependency_up",
    "Dependency status, 1 for up and 0 for down",
    ["dependency"],
)


async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    path = request.scope.get("route").path if request.scope.get("route") else request.url.path
    status = str(response.status_code)
    REQUEST_COUNT.labels(request.method, path, status).inc()
    REQUEST_DURATION.labels(request.method, path).observe(time.perf_counter() - start)
    if response.status_code >= 400:
        HTTP_ERRORS.labels(request.method, path, status).inc()
    response.headers["X-Backend-Instance"] = getattr(request.app.state, "instance_id", "unknown")
    return response


def set_dependency_status(dependency: str, is_up: bool) -> None:
    DEPENDENCY_STATUS.labels(dependency).set(1 if is_up else 0)


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
