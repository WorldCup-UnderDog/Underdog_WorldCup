from typing import Literal

from pydantic import BaseModel, Field


class MatchupRequest(BaseModel):
    team_a: str = Field(min_length=2)
    team_b: str = Field(min_length=2)
    neutral_site: bool = True
    tournament_stage: str | None = None


class MatchupResponse(BaseModel):
    team_a: str
    team_b: str
    team_a_win_prob: float
    draw_prob: float
    team_b_win_prob: float
    upset_score: float
    predicted_winner: str
    confidence: Literal["low", "medium", "high"]
    explanation: list[str]

