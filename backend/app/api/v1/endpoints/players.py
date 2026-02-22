"""Player endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Path

from ....dependencies.services import get_player_service
from ....schemas.player import GoalkeeperWallRankingResponse, NationPlayersResponse, TopUpsetPlayersResponse
from ....services.player_service import PlayerService

router = APIRouter()


@router.get("/players/{nation}", response_model=NationPlayersResponse)
def players_by_nation(
    nation: str = Path(..., min_length=2),
    service: PlayerService = Depends(get_player_service),
) -> NationPlayersResponse:
    payload = service.players_for_nation(nation)
    if payload is None:
        raise HTTPException(status_code=404, detail=f"Nation '{nation}' not found.")
    return payload


@router.get("/players/top-upsets", response_model=TopUpsetPlayersResponse)
def top_upset_players(service: PlayerService = Depends(get_player_service)) -> TopUpsetPlayersResponse:
    return service.top_upset_players()


@router.get("/goalkeepers/wall-ranking", response_model=GoalkeeperWallRankingResponse)
def goalkeeper_wall_ranking(service: PlayerService = Depends(get_player_service)) -> GoalkeeperWallRankingResponse:
    return service.goalkeeper_wall_ranking()

