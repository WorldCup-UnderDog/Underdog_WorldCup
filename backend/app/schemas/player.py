"""Player response schemas."""

from pydantic import BaseModel, Field


class PlayerRow(BaseModel):
    name: str
    nation: str
    best_position: str
    club: str
    overall_rating: str
    potential: str
    age: str


class NationPlayersResponse(BaseModel):
    nation: str
    count: int = Field(..., ge=0)
    players: list[PlayerRow]


class TopUpsetPlayer(BaseModel):
    name: str
    nation: str
    best_position: str
    club: str
    overall_rating: str
    potential: str
    development_gap: int


class TopUpsetPlayersResponse(BaseModel):
    players: list[TopUpsetPlayer]


class GoalkeeperWallRow(BaseModel):
    name: str
    nation: str
    club: str
    overall_rating: str
    potential: str


class GoalkeeperWallRankingResponse(BaseModel):
    goalkeepers: list[GoalkeeperWallRow]

