"""Prediction request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MatchPredictionRequest(BaseModel):
    team_a: str = Field(..., min_length=2)
    team_b: str = Field(..., min_length=2)
    neutral_site: bool = True


class MatchPredictionResponse(BaseModel):
    team_a: str
    team_b: str
    team_a_win_prob: int = Field(..., ge=0, le=100)
    draw_prob: int = Field(..., ge=0, le=100)
    team_b_win_prob: int = Field(..., ge=0, le=100)
    predicted_winner: str
    upset_score: int = Field(..., ge=0, le=100)
    confidence: str
    explanation: list[str]
    neutral_site: bool
    model_source: str


class UpsetRequest(BaseModel):
    team_a: str = Field(..., min_length=2)
    team_b: str = Field(..., min_length=2)
    score_a: int = Field(..., ge=0)
    score_b: int = Field(..., ge=0)
    neutral_site: bool = True


class UpsetResponse(BaseModel):
    team_a: str
    team_b: str
    score_a: int
    score_b: int
    upset_score: int = Field(..., ge=0, le=100)
    projected_result: str
    explanation: list[str]

