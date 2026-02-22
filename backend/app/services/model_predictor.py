from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


class ModelPredictorError(Exception):
    """Base exception for model predictor failures."""


class ModelNotLoadedError(ModelPredictorError):
    """Raised when inference is attempted before model artifacts are available."""


@dataclass(frozen=True)
class MatchFeatures:
    """Input features for a single team-vs-team prediction."""

    team_a_code: str
    team_b_code: str
    neutral_site: bool = True
    tournament_stage: str | None = None


@dataclass(frozen=True)
class ProbabilityPrediction:
    """Prediction outputs used by API response mapping."""

    team_a_win_prob: float
    team_b_win_prob: float


class ModelPredictor:
    """
    Wrapper for your XGBoost + linear predictor stack.

    Replace TODO blocks with your artifact loading and feature pipeline.
    """

    def __init__(self) -> None:
        self._xgb_model: Any | None = None
        self._linear_model: Any | None = None
        self._is_loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    def load_artifacts(
        self,
        *,
        xgb_model_path: Path | None = None,
        linear_model_path: Path | None = None,
    ) -> None:
        """
        Load model artifacts into memory.

        Args:
            xgb_model_path: Optional path to serialized XGBoost model.
            linear_model_path: Optional path to serialized linear model.
        """
        # TODO: Implement artifact loading.
        # Example options:
        # - xgboost.Booster().load_model(...)
        # - joblib.load(...)
        # - pickle.load(...)
        _ = xgb_model_path
        _ = linear_model_path

        self._xgb_model = None
        self._linear_model = None
        self._is_loaded = True

    def build_features(self, features: MatchFeatures) -> Mapping[str, float]:
        """
        Build model-ready feature dict/vector from matchup input.

        Return format should match what your model expects.
        """
        # TODO: Replace this placeholder mapping with your real feature engineering.
        return {
            "neutral_site": 1.0 if features.neutral_site else 0.0,
        }

    def predict(self, features: MatchFeatures) -> ProbabilityPrediction:
        """
        Run inference and return two-way probabilities.

        Output probabilities should sum to 1.0.
        """
        if not self._is_loaded:
            raise ModelNotLoadedError(
                "Model artifacts are not loaded. Call load_artifacts() first."
            )

        feature_values = self.build_features(features)

        # TODO: Replace with real inference using self._xgb_model and self._linear_model.
        # For now this is a deterministic fallback to keep integration safe.
        _ = feature_values
        team_a_prob = 0.5
        team_b_prob = 0.5

        total = team_a_prob + team_b_prob
        if total <= 0:
            raise ModelPredictorError("Model returned invalid probability totals.")

        team_a_prob = float(team_a_prob / total)
        team_b_prob = float(team_b_prob / total)

        return ProbabilityPrediction(
            team_a_win_prob=round(team_a_prob, 6),
            team_b_win_prob=round(team_b_prob, 6),
        )
