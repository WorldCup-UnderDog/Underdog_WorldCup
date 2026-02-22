"""Health endpoints."""

from fastapi import APIRouter, Depends

from ....dependencies.services import get_prediction_service
from ....schemas.common import HealthResponse
from ....services.predictor import PredictionService

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check(service: PredictionService = Depends(get_prediction_service)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        model_loaded=service.is_ready,
        model_source=service.model_source,
    )

