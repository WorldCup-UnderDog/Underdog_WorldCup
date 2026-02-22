"""Team endpoints."""

from fastapi import APIRouter, Depends

from ....dependencies.services import get_prediction_service
from ....schemas.team import TeamListResponse
from ....services.predictor import PredictionService

router = APIRouter()


@router.get("/teams", response_model=TeamListResponse)
def get_teams(service: PredictionService = Depends(get_prediction_service)) -> TeamListResponse:
    return TeamListResponse(teams=service.list_teams())

