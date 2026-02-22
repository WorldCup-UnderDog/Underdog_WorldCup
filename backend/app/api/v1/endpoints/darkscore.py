"""DarkScore endpoints — XGBoost/Elo/FC prediction pipeline."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from ....dependencies.services import get_model_service
from ....schemas.darkscore import (
    DarkScoreRequest,
    DarkScoreResponse,
    DemoPredictionsResponse,
    EloCompareRequest,
    EloCompareResponse,
)

router = APIRouter()


@router.post("/dark-score", response_model=DarkScoreResponse)
def predict_dark_score(
    payload: DarkScoreRequest,
    service: Any = Depends(get_model_service),
) -> DarkScoreResponse:
    try:
        result = service.predict_dark_score(
            home_team=payload.home_team,
            away_team=payload.away_team,
            stage_name=payload.stage_name,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    fc = result.get("fc_adjustment", {})
    dark_knight = result.get("dark_knight", {})
    return DarkScoreResponse(
        home_team=result["home_team"],
        away_team=result["away_team"],
        favorite_by_elo=result["favorite_by_elo"],
        underdog_by_elo=result["underdog_by_elo"],
        elo_home_pre=result["elo_home_pre"],
        elo_away_pre=result["elo_away_pre"],
        p_model=result["p_model"],
        p_model_raw=result["p_model_raw"],
        p_final=result["p_final"],
        dark_score=result["DarkScore"],
        alert=result["Alert"],
        fc_adjustment={
            "used_fc": fc.get("used_fc", False),
            "reason": fc.get("reason", ""),
            "z_star": fc.get("z_star"),
            "z_team": fc.get("z_team"),
            "delta_logit": fc.get("delta_logit", 0.0),
        },
        explanations=result.get("explanations", []),
        risk_band=result.get("risk_band", "Watchlist"),
        impact_level=result.get("impact_level", "Volatile"),
        fan_summary=result.get("fan_summary", "Model summary unavailable."),
        fan_takeaways=result.get("fan_takeaways", []),
        dark_knight={
            "team": dark_knight.get("team", "Data missing"),
            "player_name": dark_knight.get("player_name", "Data missing"),
            "position": dark_knight.get("position", "Data missing"),
            "skill_score": int(dark_knight.get("skill_score", 0) or 0),
            "reason": dark_knight.get("reason", "No player-impact summary available."),
        },
    )


@router.get("/demo-predictions", response_model=DemoPredictionsResponse)
def get_demo_predictions(
    service: Any = Depends(get_model_service),
) -> DemoPredictionsResponse:
    rows = service.get_demo_predictions()
    predictions = []
    for r in rows:
        predictions.append({
            "home_team": r.get("home_team", ""),
            "away_team": r.get("away_team", ""),
            "favorite_by_elo": r.get("favorite_by_elo", ""),
            "underdog_by_elo": r.get("underdog_by_elo", ""),
            "p_final": float(r.get("p_final") or 0.0),
            "dark_score": int(r.get("dark_score") or r.get("DarkScore") or 0),
            "alert": bool(r.get("alert") or r.get("Alert") or False),
            "fc_used": bool(r.get("fc_used") or False),
            "external_elo_home": r.get("external_elo_home"),
            "external_elo_away": r.get("external_elo_away"),
            "external_p_home_win": r.get("external_p_home_win"),
            "external_p_away_win": r.get("external_p_away_win"),
        })
    return DemoPredictionsResponse(predictions=predictions)


@router.post("/elo/compare", response_model=EloCompareResponse)
def compare_elo(
    payload: EloCompareRequest,
    service: Any = Depends(get_model_service),
) -> EloCompareResponse:
    result = service.compare_elo(payload.team_a, payload.team_b)
    return EloCompareResponse(**result)
