"""Prediction endpoints."""

from fastapi import APIRouter, Depends, HTTPException

from ....dependencies.services import get_prediction_service
from ....schemas.predict import (
    MatchPredictionRequest,
    MatchPredictionResponse,
    UpsetRequest,
    UpsetResponse,
)
from ....services.predictor import PredictionInputError, PredictionService

router = APIRouter()


@router.post("/predict-matchup", response_model=MatchPredictionResponse)
def predict_matchup(
    payload: MatchPredictionRequest,
    service: PredictionService = Depends(get_prediction_service),
) -> MatchPredictionResponse:
    try:
        return service.predict_matchup(payload)
    except PredictionInputError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/predict", response_model=MatchPredictionResponse)
def predict_legacy(
    payload: MatchPredictionRequest,
    service: PredictionService = Depends(get_prediction_service),
) -> MatchPredictionResponse:
    try:
        return service.predict_matchup(payload)
    except PredictionInputError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/upset", response_model=UpsetResponse)
def predict_upset_score(
    payload: UpsetRequest,
    service: PredictionService = Depends(get_prediction_service),
) -> UpsetResponse:
    try:
        return service.scoreline_upset(payload)
    except PredictionInputError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
