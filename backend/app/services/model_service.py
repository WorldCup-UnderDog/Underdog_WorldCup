"""ModelService: wraps model_predictor.py for use as an injected FastAPI service."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)

_MODEL_IMPORT_ERROR: Exception | None = None

try:
    from .model_predictor import (
        OUT_DIR,
        TEAMS_ELO_PATH,
        TOP10_FC_PATH,
        apply_slug,
        build_hypothetical_pre_match_features,
        compare_external_elo,
        dark_score_payload,
        load_artifacts_for_inference,
        load_external_elo,
        load_fc_team_table,
        predict_upset_probability,
    )
except Exception as exc:  # optional DarkScore dependency gate
    _MODEL_IMPORT_ERROR = exc
    OUT_DIR = ""
    TEAMS_ELO_PATH = ""
    TOP10_FC_PATH = ""
    apply_slug = None
    build_hypothetical_pre_match_features = None
    compare_external_elo = None
    dark_score_payload = None
    load_artifacts_for_inference = None
    load_external_elo = None
    load_fc_team_table = None
    predict_upset_probability = None

_FC26_PLAYERS_PATH = Path(__file__).parent / "Cleaned_Data" / "fc26_players_clean.csv"


def _slug_key(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if callable(apply_slug):
        return apply_slug(raw)
    return raw.lower().replace(" ", "_")


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lower_map = {c.lower(): c for c in df.columns}
    for candidate in candidates:
        col = lower_map.get(candidate.lower())
        if col is not None:
            return col
    return None


def _load_top_player_by_team(csv_path: Path) -> dict[str, dict[str, Any]]:
    if not csv_path.exists():
        logger.warning("Dark Knight player source missing: %s", csv_path)
        return {}

    try:
        players = pd.read_csv(csv_path)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to read Dark Knight player source: %s", exc)
        return {}

    team_col = _find_column(players, ["nation_slug", "nation", "team_slug", "country", "team"])
    name_col = _find_column(players, ["name", "player_name", "short_name"])
    pos_col = _find_column(players, ["best_position", "position", "club_position"])
    skill_col = _find_column(players, ["overall_rating", "best_overall", "overall", "potential"])

    if team_col is None or name_col is None:
        logger.warning("Dark Knight player source missing required columns: team/name")
        return {}

    df = players.copy()
    df["_team_key"] = df[team_col].astype(str).map(_slug_key)
    df["_name"] = df[name_col].fillna("Data missing").astype(str).str.strip()
    if pos_col is None:
        df["_position"] = "Data missing"
    else:
        df["_position"] = df[pos_col].fillna("Data missing").astype(str).str.strip()
    if skill_col is None:
        df["_skill_score"] = 0.0
    else:
        df["_skill_score"] = pd.to_numeric(df[skill_col], errors="coerce").fillna(0.0)

    df = df[df["_team_key"] != ""].copy()
    if df.empty:
        logger.warning("Dark Knight player source parsed but team keys were empty.")
        return {}

    top_idx = df.groupby("_team_key")["_skill_score"].idxmax()
    top_rows = df.loc[top_idx, ["_team_key", "_name", "_position", "_skill_score"]]

    by_team: dict[str, dict[str, Any]] = {}
    for _, row in top_rows.iterrows():
        try:
            score = float(row["_skill_score"])
        except Exception:  # noqa: BLE001
            score = 0.0
        by_team[str(row["_team_key"])] = {
            "player_name": str(row["_name"]) or "Data missing",
            "position": str(row["_position"]) or "Data missing",
            "skill_score": int(max(0, min(100, round(score)))),
        }

    logger.info("Loaded Dark Knight player map: teams=%s source=%s", len(by_team), csv_path.name)
    return by_team


def _risk_band(score: int) -> tuple[str, str]:
    if score < 40:
        return "Low upset risk", "Stable"
    if score < 60:
        return "Watchlist", "Volatile"
    return "Upset alert", "High impact"


def _fan_takeaways(
    *,
    score: int,
    upset_pct: int,
    favorite_team: str,
    underdog_team: str,
) -> tuple[str, list[str]]:
    if score < 40:
        summary = f"{favorite_team} control this matchup in most simulations ({upset_pct}% upset path)."
        return summary, [
            f"{favorite_team} have the stronger baseline profile.",
            f"{underdog_team} likely need a standout individual performance to flip this.",
            "Use this as a lower-risk pick, not a guaranteed result.",
        ]

    if score < 60:
        summary = f"This matchup is live ({upset_pct}% upset path) and can swing on one moment."
        return summary, [
            f"{favorite_team} are still the safer side, but not by much.",
            f"{underdog_team} have a realistic route to avoid defeat.",
            "Treat this as a watchlist fixture for bracket strategy.",
        ]

    summary = f"High upset pressure ({upset_pct}% upset path): {underdog_team} can realistically avoid losing."
    return summary, [
        f"{favorite_team} still carry pedigree, but their edge is fragile here.",
        f"{underdog_team} have enough quality to turn this matchup.",
        "This sits in the upset-alert tier of DarkScore.",
    ]


@dataclass
class ModelService:
    xgb_model: Any
    calibrator: Any
    feature_info: dict
    fc_team: pd.DataFrame
    external_elo_map: dict[str, float]
    top_player_by_team: dict[str, dict[str, Any]]
    alert_threshold: float = 0.60
    _demo_csv: Path = field(init=False)

    def __post_init__(self) -> None:
        self._demo_csv = Path(OUT_DIR) / "demo_predictions_top10.csv"

    def predict_dark_score(self, home_team: str, away_team: str, stage_name: str = "group stage") -> dict:
        if _MODEL_IMPORT_ERROR is not None:
            raise RuntimeError("DarkScore model dependencies are unavailable on this server.")

        feature_cols = list(self.feature_info["feature_columns"])
        fit_medians = pd.Series(self.feature_info["fit_medians"], dtype=float)
        last_team_state = dict(self.feature_info.get("last_team_state", {}))
        last_elo_end = {k: float(v) for k, v in self.feature_info.get("last_elo_end", {}).items()}
        use_goals = bool(self.feature_info.get("use_goals_features", False))

        feature_row = build_hypothetical_pre_match_features(
            home_team_name=home_team,
            away_team_name=away_team,
            last_team_state=last_team_state,
            last_elo_end=last_elo_end,
            use_goals_features=use_goals,
            stage_name=stage_name,
        )

        p_model, p_raw = predict_upset_probability(
            feature_row=feature_row,
            xgb_model=self.xgb_model,
            calibrator=self.calibrator,
            feature_cols=feature_cols,
            fit_medians=fit_medians,
        )

        payload = dark_score_payload(
            feature_row=feature_row,
            p_model=p_model,
            p_raw=p_raw,
            fc_team=self.fc_team,
            alert_threshold=self.alert_threshold,
        )

        # Attach Elo values for the UI
        payload["elo_home_pre"] = float(feature_row["elo_home_pre"])
        payload["elo_away_pre"] = float(feature_row["elo_away_pre"])
        dark_score = int(payload.get("DarkScore", 0))
        upset_pct = int(round(float(payload.get("p_final", 0.0)) * 100.0))
        favorite = str(payload.get("favorite_by_elo", home_team))
        underdog = str(payload.get("underdog_by_elo", away_team))
        risk_band, impact_level = _risk_band(dark_score)
        summary, takeaways = _fan_takeaways(
            score=dark_score,
            upset_pct=upset_pct,
            favorite_team=favorite,
            underdog_team=underdog,
        )
        payload["risk_band"] = risk_band
        payload["impact_level"] = impact_level
        payload["fan_summary"] = summary
        payload["fan_takeaways"] = takeaways
        payload["dark_knight"] = self._resolve_dark_knight(
            home_team=str(payload.get("home_team", home_team)),
            away_team=str(payload.get("away_team", away_team)),
            favorite_team=favorite,
            underdog_team=underdog,
            dark_score=dark_score,
        )
        return payload

    def _resolve_dark_knight(
        self,
        *,
        home_team: str,
        away_team: str,
        favorite_team: str,
        underdog_team: str,
        dark_score: int,
    ) -> dict[str, Any]:
        home_player = self.top_player_by_team.get(_slug_key(home_team))
        away_player = self.top_player_by_team.get(_slug_key(away_team))

        if home_player is None and away_player is None:
            return {
                "team": "Data missing",
                "player_name": "Data missing",
                "position": "Data missing",
                "skill_score": 0,
                "reason": "Player-skill source is missing for both teams.",
            }

        if away_player is None or (home_player is not None and home_player["skill_score"] >= away_player["skill_score"]):
            chosen_team = home_team
            chosen_player = home_player
            missing_opponent = away_player is None
        else:
            chosen_team = away_team
            chosen_player = away_player
            missing_opponent = home_player is None

        if chosen_player is None:
            return {
                "team": "Data missing",
                "player_name": "Data missing",
                "position": "Data missing",
                "skill_score": 0,
                "reason": "Player-skill source was found but did not map to this matchup.",
            }

        if missing_opponent:
            reason = f"{chosen_team}'s top player is highlighted because the opposing team has missing player-skill rows."
        elif chosen_team == underdog_team and dark_score >= 60:
            reason = f"{chosen_team}'s top player is the key upset lever in this matchup."
        elif chosen_team == favorite_team and dark_score < 40:
            reason = f"{chosen_team}'s top player reinforces favorite control in this matchup."
        else:
            reason = f"{chosen_team}'s top player has the highest available skill score across both squads."

        return {
            "team": chosen_team,
            "player_name": chosen_player.get("player_name", "Data missing"),
            "position": chosen_player.get("position", "Data missing"),
            "skill_score": int(chosen_player.get("skill_score", 0)),
            "reason": reason,
        }

    def compare_elo(self, team_a: str, team_b: str) -> dict:
        if _MODEL_IMPORT_ERROR is not None:
            raise RuntimeError("DarkScore model dependencies are unavailable on this server.")
        return compare_external_elo(team_a, team_b, self.external_elo_map)

    def get_demo_predictions(self) -> list[dict]:
        if not self._demo_csv.exists():
            return []
        df = pd.read_csv(self._demo_csv)
        # Normalise column names to match schema
        rename = {"DarkScore": "dark_score", "Alert": "alert"}
        df = df.rename(columns=rename)
        # Fill NaN with None-compatible values
        records = df.where(pd.notnull(df), other=None).to_dict(orient="records")
        return records


def load_model_service() -> ModelService | None:
    """Load model artifacts from disk. Returns None and logs a warning on failure."""
    if _MODEL_IMPORT_ERROR is not None:
        logger.warning("ModelService disabled: %s", _MODEL_IMPORT_ERROR)
        return None

    try:
        xgb_model, calibrator, feature_info = load_artifacts_for_inference(OUT_DIR)
        fc_team = load_fc_team_table(TOP10_FC_PATH)
        external_elo_map = load_external_elo(TEAMS_ELO_PATH)
        top_player_by_team = _load_top_player_by_team(_FC26_PLAYERS_PATH)
        return ModelService(
            xgb_model=xgb_model,
            calibrator=calibrator,
            feature_info=feature_info,
            fc_team=fc_team,
            external_elo_map=external_elo_map,
            top_player_by_team=top_player_by_team,
            alert_threshold=float(feature_info.get("alert_threshold", 0.60)),
        )
    except Exception as exc:
        logger.warning("ModelService could not be loaded: %s", exc)
        return None
