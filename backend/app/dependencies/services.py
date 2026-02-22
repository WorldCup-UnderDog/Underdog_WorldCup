"""Service dependencies."""

from fastapi import Request

from ..services.player_service import PlayerService
from ..services.predictor import PredictionService


def get_prediction_service(request: Request) -> PredictionService:
    return request.app.state.prediction_service


def get_player_service(request: Request) -> PlayerService:
    return request.app.state.player_service

