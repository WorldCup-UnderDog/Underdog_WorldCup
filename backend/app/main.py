"""FastAPI app entrypoint."""

from __future__ import annotations

import pandas as pd
from typing import Literal
import sys, os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .api.v1.router import api_router
from .core.config import settings
from .core.logging import configure_logging
from .services.data_loader import load_matchup_dataset, load_player_records
from .services.player_service import PlayerService
from .services.predictor import PredictionService

# ── Load player data ─────────────────────────────────────
players_df = pd.read_csv(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data/fc26_combined.csv")
)
players_df = players_df[players_df["name"].notna() & players_df["overall_rating"].notna()]

# ── Lifespan ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    matchup_dataset = load_matchup_dataset()
    player_records = load_player_records()
    app.state.prediction_service = PredictionService(dataset=matchup_dataset)
    app.state.player_service = PlayerService(players=player_records)
    yield

# ── App ───────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(api_router, prefix="/api/v1")

# ── Player endpoints ──────────────────────────────────────
@app.get("/players")
def get_players(nation: str = None, position: str = None):
    df = players_df.copy()
    if nation:
        df = df[df["nation"].str.lower().str.strip() == nation.lower().strip()]
    if position:
        df = df[df["best_position"].str.upper() == position.upper()]
    df = df.sort_values("overall_rating", ascending=False)
    return df[[
        "name", "nation", "best_position", "age",
        "overall_rating", "potential", "value",
        "playstyles", "playstyles2", "playstyles3",
        "acceleration", "sprint_speed", "dribbling", "finishing",
        "short_passing", "long_passing",
        "total_attacking", "total_skill", "total_movement",
        "total_power", "total_mentality", "total_defending",
        "total_goalkeeping", "reactions", "heading_accuracy",
        "ball_control", "jumping"
    ]].fillna(0).to_dict(orient="records")

@app.get("/player/{name}")
def get_player(name: str):
    row = players_df[players_df["name"].str.lower() == name.lower()]
    if row.empty:
        return {"error": "Player not found"}
    return row.iloc[0].fillna(0).to_dict()