"""Service dependencies."""

from typing import Any

from fastapi import HTTPException, Request

from ..services.player_service import PlayerService
from ..services.predictor import PredictionService


def get_prediction_service(request: Request) -> PredictionService:
    return request.app.state.prediction_service


def get_player_service(request: Request) -> PlayerService:
    return request.app.state.player_service


def get_model_service(request: Request) -> Any:
    svc = getattr(request.app.state, "model_service", None)
    if svc is None:
        raise HTTPException(status_code=503, detail="ML model not loaded — run model_predictor.py --all first.")
    return svc
