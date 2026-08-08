from fastapi import APIRouter

from app.services.metrics import metrics_response


router = APIRouter(tags=["metrics"])


@router.get("/metrics", summary="Prometheus metrics")
def metrics():
    return metrics_response()
