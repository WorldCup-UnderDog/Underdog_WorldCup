"""DarkScore request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class DarkScoreRequest(BaseModel):
    home_team: str = Field(..., min_length=2)
    away_team: str = Field(..., min_length=2)
    stage_name: str = "group stage"


class FCDetails(BaseModel):
    used_fc: bool
    reason: str
    z_star: float | None = None
    z_team: float | None = None
    delta_logit: float = 0.0


class DarkKnight(BaseModel):
    team: str
    player_name: str
    position: str
    skill_score: int = Field(..., ge=0, le=100)
    reason: str


class DarkScoreResponse(BaseModel):
    home_team: str
    away_team: str
    favorite_by_elo: str
    underdog_by_elo: str
    elo_home_pre: float
    elo_away_pre: float
    p_model: float
    p_model_raw: float
    p_final: float
    dark_score: float = Field(..., ge=0, le=100)
    alert: bool
    fc_adjustment: FCDetails
    explanations: list[str]
    risk_band: str
    impact_level: str
    fan_summary: str
    fan_takeaways: list[str]
    dark_knight_rule: str
    dark_knight_team: str
    dark_knight: DarkKnight
    dark_knights: list[DarkKnight]


class EloCompareRequest(BaseModel):
    team_a: str
    team_b: str


class EloCompareResponse(BaseModel):
    team_a_slug: str
    team_b_slug: str
    elo_a: float | None = None
    elo_b: float | None = None
    higher_team: str | None = None
    p_a_win: float | None = None
    p_b_win: float | None = None
    pct_point_advantage: float | None = None


class DemoPredictionRow(BaseModel):
    home_team: str
    away_team: str
    favorite_by_elo: str
    underdog_by_elo: str
    p_final: float
    dark_score: float
    alert: bool
    fc_used: bool
    external_elo_home: float | None = None
    external_elo_away: float | None = None
    external_p_home_win: float | None = None
    external_p_away_win: float | None = None
    description: str | None = None
    focus_players: list[str] = Field(default_factory=list)


class DemoPredictionsResponse(BaseModel):
    predictions: list[DemoPredictionRow]
