from fastapi import APIRouter

from backend.core.model_metrics import MODEL_METRICS
from backend.models.schemas import ModelMetricsResponse

router = APIRouter(tags=["model"])


@router.get("/model-metrics", response_model=ModelMetricsResponse)
def get_model_metrics() -> ModelMetricsResponse:
    return ModelMetricsResponse(**MODEL_METRICS)
