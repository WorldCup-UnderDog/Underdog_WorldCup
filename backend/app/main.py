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
from .services.model_service import load_model_service
from .services.player_service import PlayerService
from .services.predictor import PredictionService

# ── Load player data ─────────────────────────────────────
players_df = pd.read_csv(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data/fc26_combined.csv")
)
players_df = players_df[players_df["name"].notna() & players_df["overall_rating"].notna()]

# Fill nulls with position-group medians so stat columns never return 0 for missing data
_POS_GROUPS = {
    "GK":  ["GK"],
    "DEF": ["CB", "LB", "RB", "LWB", "RWB"],
    "MID": ["CM", "CDM", "CAM", "LM", "RM"],
    "FWD": ["ST", "CF", "LW", "RW"],
}
_pos_to_group = {pos: grp for grp, positions in _POS_GROUPS.items() for pos in positions}
_stat_cols = [
    "acceleration", "sprint_speed", "dribbling", "finishing",
    "short_passing", "long_passing", "reactions", "heading_accuracy",
    "ball_control", "agility", "balance", "shot_power", "jumping",
    "total_goalkeeping", "total_defending", "total_power",
    "total_mentality", "total_attacking", "total_skill", "total_movement",
]
_stat_cols = [c for c in _stat_cols if c in players_df.columns]
players_df["_pos_group"] = players_df["best_position"].map(_pos_to_group).fillna("MID")
for _col in _stat_cols:
    _group_medians = players_df.groupby("_pos_group")[_col].transform("median")
    players_df[_col] = players_df[_col].fillna(_group_medians).fillna(players_df[_col].median())
players_df.drop(columns=["_pos_group"], inplace=True)

# ── Lifespan ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    matchup_dataset = load_matchup_dataset()
    player_records = load_player_records()
    app.state.prediction_service = PredictionService(dataset=matchup_dataset)
    app.state.player_service = PlayerService(players=player_records)
    app.state.model_service = load_model_service()  # None if artifacts missing
    yield

# ── App ───────────────────────────────────────────────────
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
