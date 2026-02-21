from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.schemas import MatchupRequest, MatchupResponse
from app.services.data_loader import (
    NAME_TO_CODE,
    default_matchup_csv_path,
    extract_supported_codes,
    load_matchup_lookup,
)
from app.services.predictor import (
    InvalidMatchupError,
    MatchupNotFoundError,
    MatchupPredictor,
    UnknownTeamError,
    UnsupportedTeamError,
)

app = FastAPI(title="Dark Horse Matchup API", version="0.1.0")

# Local-dev CORS. Restrict in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class HealthResponse(BaseModel):
    status: str
    matchup_pairs: int
    supported_teams: int


class TeamsResponse(BaseModel):
    teams: list[str]


def _resolve_matchup_csv_path() -> Path:
    configured_path = os.getenv("MATCHUP_CSV_PATH", "").strip()
    if not configured_path:
        return default_matchup_csv_path()
    path = Path(configured_path).expanduser()
    if not path.is_absolute():
        path = (Path(__file__).resolve().parents[1] / path).resolve()
    return path


def _build_predictor() -> MatchupPredictor:
    csv_path = _resolve_matchup_csv_path()
    lookup = load_matchup_lookup(csv_path)
    supported_codes = extract_supported_codes(lookup)
    return MatchupPredictor(
        lookup=lookup,
        name_to_code=NAME_TO_CODE,
        supported_codes=supported_codes,
    )


predictor = _build_predictor()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        matchup_pairs=predictor.matchup_count,
        supported_teams=len(predictor.supported_team_names()),
    )


@app.get("/teams", response_model=TeamsResponse)
def teams() -> TeamsResponse:
    return TeamsResponse(teams=predictor.supported_team_names())


@app.post("/predict-matchup", response_model=MatchupResponse)
def predict_matchup(req: MatchupRequest) -> MatchupResponse:
    try:
        return predictor.predict(req)
    except InvalidMatchupError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except UnknownTeamError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except UnsupportedTeamError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except MatchupNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
