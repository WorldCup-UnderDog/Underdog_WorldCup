"""Player-focused API service methods."""

from __future__ import annotations

from dataclasses import dataclass

from ..schemas.player import (
    GoalkeeperWallRankingResponse,
    GoalkeeperWallRow,
    NationPlayersResponse,
    PlayerRow,
    TopUpsetPlayer,
    TopUpsetPlayersResponse,
)
from .data_loader import PlayerRecord, normalize_text


def _to_int(raw: str, fallback: int = 0) -> int:
    try:
        return int(float(raw))
    except (TypeError, ValueError):
        return fallback


@dataclass
class PlayerService:
    players: list[PlayerRecord]

    def players_for_nation(self, nation: str) -> NationPlayersResponse | None:
        nation_key = normalize_text(nation)
        matched = [player for player in self.players if normalize_text(player.nation) == nation_key]
        if not matched:
            return None

        rows = [
            PlayerRow(
                name=player.name,
                nation=player.nation,
                best_position=player.best_position,
                club=player.club,
                overall_rating=player.overall_rating,
                potential=player.potential,
                age=player.age,
            )
            for player in sorted(matched, key=lambda item: (_to_int(item.overall_rating), _to_int(item.potential)), reverse=True)
        ]
        return NationPlayersResponse(nation=rows[0].nation, count=len(rows), players=rows)

    def top_upset_players(self, limit: int = 20) -> TopUpsetPlayersResponse:
        ranked = sorted(
            self.players,
            key=lambda player: (_to_int(player.potential) - _to_int(player.overall_rating), _to_int(player.potential)),
            reverse=True,
        )[:limit]
        payload = [
            TopUpsetPlayer(
                name=player.name,
                nation=player.nation,
                best_position=player.best_position,
                club=player.club,
                overall_rating=player.overall_rating,
                potential=player.potential,
                development_gap=max(0, _to_int(player.potential) - _to_int(player.overall_rating)),
            )
            for player in ranked
        ]
        return TopUpsetPlayersResponse(players=payload)

    def goalkeeper_wall_ranking(self, limit: int = 20) -> GoalkeeperWallRankingResponse:
        keepers = [
            player
            for player in self.players
            if normalize_text(player.best_position) == "gk"
        ]
        keepers = sorted(keepers, key=lambda player: (_to_int(player.overall_rating), _to_int(player.potential)), reverse=True)[:limit]
        payload = [
            GoalkeeperWallRow(
                name=player.name,
                nation=player.nation,
                club=player.club,
                overall_rating=player.overall_rating,
                potential=player.potential,
            )
            for player in keepers
        ]
        return GoalkeeperWallRankingResponse(goalkeepers=payload)

