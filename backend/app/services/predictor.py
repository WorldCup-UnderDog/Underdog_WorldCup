from __future__ import annotations

from typing import Literal, Mapping

from app.schemas import MatchupRequest, MatchupResponse


class PredictionError(Exception):
    """Base class for prediction failures."""


class UnknownTeamError(PredictionError):
    """Raised when a team name is not in the name->code mapping."""


class UnsupportedTeamError(PredictionError):
    """Raised when a mapped team code does not exist in the model data."""


class MatchupNotFoundError(PredictionError):
    """Raised when the directed or reverse matchup is missing."""


class InvalidMatchupError(PredictionError):
    """Raised when the request has invalid matchup inputs."""


class MatchupPredictor:
    def __init__(
        self,
        lookup: Mapping[tuple[str, str], float],
        name_to_code: Mapping[str, str],
        supported_codes: set[str],
    ) -> None:
        self._lookup = dict(lookup)
        self._name_to_code = dict(name_to_code)
        self._supported_codes = set(supported_codes)

    @property
    def matchup_count(self) -> int:
        return len(self._lookup)

    def supported_team_names(self) -> list[str]:
        names_by_code: dict[str, str] = {}
        for name, code in self._name_to_code.items():
            if code in self._supported_codes and code not in names_by_code:
                names_by_code[code] = name
        return list(names_by_code.values())

    def predict(self, req: MatchupRequest) -> MatchupResponse:
        team_a = req.team_a.strip()
        team_b = req.team_b.strip()
        if team_a == team_b:
            raise InvalidMatchupError("team_a and team_b must be different.")

        code_a = self._name_to_code.get(team_a)
        code_b = self._name_to_code.get(team_b)
        if code_a is None:
            raise UnknownTeamError(f"Unsupported team name for team_a: '{team_a}'.")
        if code_b is None:
            raise UnknownTeamError(f"Unsupported team name for team_b: '{team_b}'.")
        if code_a not in self._supported_codes:
            raise UnsupportedTeamError(
                f"No model data available for team_a: '{team_a}' ({code_a})."
            )
        if code_b not in self._supported_codes:
            raise UnsupportedTeamError(
                f"No model data available for team_b: '{team_b}' ({code_b})."
            )

        p_a, p_b = self._win_probabilities(code_a, code_b)

        # Light home adjustment for team A when not neutral.
        if not req.neutral_site:
            p_a = min(0.98, p_a + 0.03)
            p_b = round(1.0 - p_a, 6)

        draw, win_a, win_b = self._three_way_percentages(p_a, p_b)

        gap = abs(p_a - p_b)
        predicted_winner = team_a if p_a >= p_b else team_b
        underdog = team_b if p_a >= p_b else team_a
        underdog_prob = min(p_a, p_b)

        confidence: Literal["low", "medium", "high"]
        if gap > 0.25:
            confidence = "high"
        elif gap > 0.10:
            confidence = "medium"
        else:
            confidence = "low"

        # Upset score on 0-100 scale: closer matchups imply higher upset potential.
        upset_score = round(max(0.0, min(100.0, 100.0 - (gap * 200))), 1)
        explanation = [
            f"Historical model matchup rates favor {predicted_winner}.",
            f"Win probability split: {team_a} {win_a}% / Draw {draw}% / {team_b} {win_b}%.",
            f"Neutral site is set to {req.neutral_site}.",
        ]
        if underdog_prob < 0.35:
            explanation.append(f"A win for {underdog} would be a notable upset.")

        return MatchupResponse(
            team_a=team_a,
            team_b=team_b,
            team_a_win_prob=win_a,
            draw_prob=draw,
            team_b_win_prob=win_b,
            upset_score=upset_score,
            predicted_winner=predicted_winner,
            confidence=confidence,
            explanation=explanation,
        )

    def _win_probabilities(self, code_a: str, code_b: str) -> tuple[float, float]:
        forward = (code_a, code_b)
        reverse = (code_b, code_a)
        if forward in self._lookup:
            p_a = self._lookup[forward]
            return p_a, round(1.0 - p_a, 6)
        if reverse in self._lookup:
            p_a = round(1.0 - self._lookup[reverse], 6)
            return p_a, round(1.0 - p_a, 6)
        raise MatchupNotFoundError(
            f"No model row found for matchup '{code_a}' vs '{code_b}'."
        )

    @staticmethod
    def _three_way_percentages(p_a: float, p_b: float) -> tuple[float, float, float]:
        closeness = 1.0 - abs(p_a - p_b)
        draw = round(closeness * 18.0, 1)
        win_a = round(p_a * (100.0 - draw), 1)
        win_b = round(p_b * (100.0 - draw), 1)

        # Adjust one side for floating-point rounding to keep exact total of 100.
        remainder = round(100.0 - win_a - win_b - draw, 1)
        win_a = round(win_a + remainder, 1)
        return draw, win_a, win_b
