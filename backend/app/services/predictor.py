"""Prediction service for matchup endpoints."""

from __future__ import annotations

from dataclasses import dataclass
import math

from ..schemas.predict import MatchPredictionRequest, MatchPredictionResponse, UpsetRequest, UpsetResponse
from .data_loader import MatchupDataset, normalize_text


class PredictionInputError(ValueError):
    """Raised when the prediction request input is invalid."""


@dataclass
class PredictionService:
    dataset: MatchupDataset
    home_advantage: float = 0.04

    @property
    def is_ready(self) -> bool:
        return bool(self.dataset.probabilities)

    @property
    def model_source(self) -> str:
        return self.dataset.source_file

    def list_teams(self) -> list[str]:
        return self.dataset.teams

    def predict_matchup(self, payload: MatchPredictionRequest) -> MatchPredictionResponse:
        team_a = self._resolve_team_name(payload.team_a)
        team_b = self._resolve_team_name(payload.team_b)
        if team_a == team_b:
            raise PredictionInputError("team_a and team_b must be different.")

        raw_a, raw_b, probability_source = self._lookup_pair_probabilities(team_a, team_b)
        adj_a, adj_b = self._apply_home_adjustment(raw_a, raw_b, payload.neutral_site)

        draw_prob = self._derive_draw_probability(adj_a, adj_b, payload.neutral_site)
        win_space = max(0.0, 1.0 - draw_prob)
        total = adj_a + adj_b
        if total <= 0:
            adj_a = adj_b = 0.5
            total = 1.0

        win_a = (adj_a / total) * win_space
        win_b = (adj_b / total) * win_space

        pct_a, pct_draw, pct_b = self._to_percentages(win_a, draw_prob, win_b)
        predicted_winner = team_a if pct_a >= pct_b else team_b
        confidence = self._confidence_label(pct_a, pct_b, pct_draw)
        upset_score = self._upset_score(pct_a, pct_b)
        favorite_team, underdog_team = self._favorite_and_underdog(team_a, team_b, pct_a, pct_b)
        elo_gap = self._elo_gap(team_a, team_b)
        base_line, method_line = self._base_probability_lines(
            probability_source=probability_source,
            favorite_team=favorite_team,
            underdog_team=underdog_team,
            elo_gap=elo_gap,
        )

        explanation = [
            base_line,
            method_line,
            f"{'Neutral venue keeps baseline balance.' if payload.neutral_site else f'{team_a} receives a small home advantage boost.'}",
            f"Draw probability is adjusted by matchup parity (current draw estimate: {pct_draw}%).",
        ]

        return MatchPredictionResponse(
            team_a=team_a,
            team_b=team_b,
            team_a_win_prob=pct_a,
            draw_prob=pct_draw,
            team_b_win_prob=pct_b,
            predicted_winner=predicted_winner,
            upset_score=upset_score,
            confidence=confidence,
            explanation=explanation,
            neutral_site=payload.neutral_site,
            model_source=probability_source,
        )

    def scoreline_upset(self, payload: UpsetRequest) -> UpsetResponse:
        prediction = self.predict_matchup(
            MatchPredictionRequest(
                team_a=payload.team_a,
                team_b=payload.team_b,
                neutral_site=payload.neutral_site,
            )
        )
        goal_diff = abs(payload.score_a - payload.score_b)
        base = prediction.upset_score
        if payload.score_a == payload.score_b:
            adjusted = min(100, base + 8)
            projected = "Draw"
        else:
            picked_winner = prediction.team_a if payload.score_a > payload.score_b else prediction.team_b
            winner_matches = picked_winner == prediction.predicted_winner
            adjusted = base - min(20, goal_diff * 4) if winner_matches else min(100, base + 18 + goal_diff * 3)
            projected = picked_winner

        adjusted = max(0, min(100, int(round(adjusted))))
        return UpsetResponse(
            team_a=prediction.team_a,
            team_b=prediction.team_b,
            score_a=payload.score_a,
            score_b=payload.score_b,
            upset_score=adjusted,
            projected_result=projected,
            explanation=[
                f"Baseline upset risk from model output: {base}/100.",
                "Submitted scoreline is compared to predicted winner and margin.",
                "Contrarian scorelines increase upset score; expected scorelines lower it.",
            ],
        )

    def _resolve_team_name(self, candidate: str) -> str:
        normalized = normalize_text(candidate)
        for team in self.dataset.teams:
            if normalize_text(team) == normalized:
                return team
        raise PredictionInputError(f"Unsupported team: {candidate}")

    def _lookup_pair_probabilities(self, team_a: str, team_b: str) -> tuple[float, float, str]:
        elo_a = self.dataset.team_elo.get(team_a)
        elo_b = self.dataset.team_elo.get(team_b)
        if elo_a is not None and elo_b is not None:
            prob_a = 1.0 / (1.0 + 10 ** ((elo_b - elo_a) / 400.0))
            prob_b = 1.0 - prob_a
            return prob_a, prob_b, self.dataset.source_file

        direct = self.dataset.probabilities.get((team_a, team_b))
        if direct is not None:
            return direct[0], direct[1], self.dataset.fallback_source_file

        reversed_pair = self.dataset.probabilities.get((team_b, team_a))
        if reversed_pair is not None:
            prob_b, prob_a = reversed_pair
            return prob_a, prob_b, self.dataset.fallback_source_file

        strength_a = self.dataset.team_strength.get(team_a, 70.0)
        strength_b = self.dataset.team_strength.get(team_b, 70.0)
        diff = strength_a - strength_b
        prob_a = 1.0 / (1.0 + math.exp(-diff / 4.5))
        prob_b = 1.0 - prob_a
        return prob_a, prob_b, "fc26_combined.csv team-strength fallback"

    def _base_probability_lines(
        self,
        *,
        probability_source: str,
        favorite_team: str,
        underdog_team: str,
        elo_gap: float | None,
    ) -> tuple[str, str]:
        if probability_source == self.dataset.source_file:
            if elo_gap is None:
                base_line = "Base probabilities follow an Elo matchup template using current team rating levels."
            else:
                base_line = (
                    f"Base probabilities follow an Elo matchup template; {favorite_team} hold roughly a "
                    f"{round(elo_gap)}-point rating edge over {underdog_team}."
                )
            return (
                base_line,
                "Win likelihood increases as the Elo differential widens in favor of one side.",
            )
        if probability_source == self.dataset.fallback_source_file:
            return (
                "Base probabilities use a calibrated matchup template when Elo coverage is missing.",
                "Win likelihood is inferred from historical pair-level tendencies in the matchup matrix.",
            )
        return (
            "Base probabilities use a squad-strength template built from FC26 ratings.",
            "Win likelihood is inferred from relative team strength when direct matchup priors are unavailable.",
        )

    @staticmethod
    def _favorite_and_underdog(team_a: str, team_b: str, prob_a_pct: int, prob_b_pct: int) -> tuple[str, str]:
        favorite_team = team_a if prob_a_pct >= prob_b_pct else team_b
        underdog_team = team_b if favorite_team == team_a else team_a
        return favorite_team, underdog_team

    def _elo_gap(self, team_a: str, team_b: str) -> float | None:
        elo_a = self.dataset.team_elo.get(team_a)
        elo_b = self.dataset.team_elo.get(team_b)
        if elo_a is None or elo_b is None:
            return None
        return abs(elo_a - elo_b)

    def _apply_home_adjustment(self, prob_a: float, prob_b: float, neutral_site: bool) -> tuple[float, float]:
        if neutral_site:
            return prob_a, prob_b

        boosted_a = prob_a + self.home_advantage
        lowered_b = max(0.01, prob_b - self.home_advantage)
        total = boosted_a + lowered_b
        return boosted_a / total, lowered_b / total

    @staticmethod
    def _derive_draw_probability(prob_a: float, prob_b: float, neutral_site: bool) -> float:
        parity = 1.0 - abs(prob_a - prob_b)
        base = 0.11 if neutral_site else 0.08
        draw_prob = base + (0.16 * parity)
        return max(0.04, min(0.28, draw_prob))

    @staticmethod
    def _to_percentages(prob_a: float, prob_draw: float, prob_b: float) -> tuple[int, int, int]:
        values = [prob_a, prob_draw, prob_b]
        rounded = [int(round(value * 100)) for value in values]
        delta = 100 - sum(rounded)
        if delta != 0:
            max_idx = max(range(3), key=lambda idx: values[idx])
            rounded[max_idx] += delta
        return rounded[0], rounded[1], rounded[2]

    @staticmethod
    def _confidence_label(prob_a_pct: int, prob_b_pct: int, draw_pct: int) -> str:
        margin = abs(prob_a_pct - prob_b_pct)
        winner_prob = max(prob_a_pct, prob_b_pct)
        if winner_prob >= 68 and draw_pct <= 18 and margin >= 18:
            return "High"
        if winner_prob >= 55 and margin >= 8:
            return "Medium"
        return "Low"

    @staticmethod
    def _upset_score(prob_a_pct: int, prob_b_pct: int) -> int:
        favorite_prob = max(prob_a_pct, prob_b_pct)
        score = (100 - favorite_prob) * 1.65
        return max(0, min(100, int(round(score))))
