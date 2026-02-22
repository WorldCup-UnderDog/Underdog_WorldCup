"""FastAPI app entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.router import api_router
from .core.config import settings
from .core.logging import configure_logging
from .services.data_loader import load_matchup_dataset, load_player_records
from .services.player_service import PlayerService
from .services.predictor import PredictionService


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    matchup_dataset = load_matchup_dataset()
    player_records = load_player_records()
    app.state.prediction_service = PredictionService(dataset=matchup_dataset)
    app.state.player_service = PlayerService(players=player_records)
    yield


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(api_router, prefix="/api/v1")

