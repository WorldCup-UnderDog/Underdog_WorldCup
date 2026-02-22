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
OLD_SCORE_MIN = 40.0
OLD_SCORE_MAX = 60.0
NEW_SCORE_MIN = 15.0
NEW_SCORE_MAX = 90.0
NEW_SCORE_MEAN = (NEW_SCORE_MIN + NEW_SCORE_MAX) / 2.0


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


def _load_ranked_players_by_team(csv_path: Path, max_players_per_team: int = 5) -> dict[str, list[dict[str, Any]]]:
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

    df = df.sort_values(["_team_key", "_skill_score", "_name"], ascending=[True, False, True]).reset_index(drop=True)

    by_team: dict[str, list[dict[str, Any]]] = {}
    for team_key, group in df.groupby("_team_key", sort=False):
        players: list[dict[str, Any]] = []
        for _, row in group.head(max_players_per_team).iterrows():
            try:
                score = float(row["_skill_score"])
            except Exception:  # noqa: BLE001
                score = 0.0
            players.append({
                "player_name": str(row["_name"]) or "Data missing",
                "position": str(row["_position"]) or "Data missing",
                "skill_score": int(max(0, min(100, round(score)))),
            })
        by_team[str(team_key)] = players

    logger.info("Loaded Dark Knight player rankings: teams=%s source=%s", len(by_team), csv_path.name)
    return by_team


def _risk_band(score: float) -> tuple[str, str]:
    if score <= NEW_SCORE_MIN:
        return f"Low range (<={int(NEW_SCORE_MIN)})", "Lower upset pressure"
    if score >= NEW_SCORE_MAX:
        return f"High range (>={int(NEW_SCORE_MAX)})", "High upset pressure"
    return f"Mean range (~{NEW_SCORE_MEAN:.1f})", "Balanced upset pressure"


def _rescale_dark_score(value: float | int) -> float:
    raw = float(value)
    if OLD_SCORE_MAX == OLD_SCORE_MIN:
        return round(max(0.0, min(100.0, raw)), 1)
    scaled = NEW_SCORE_MIN + ((raw - OLD_SCORE_MIN) * (NEW_SCORE_MAX - NEW_SCORE_MIN) / (OLD_SCORE_MAX - OLD_SCORE_MIN))
    return round(max(0.0, min(100.0, scaled)), 1)


@dataclass
class ModelService:
    xgb_model: Any
    calibrator: Any
    feature_info: dict
    fc_team: pd.DataFrame
    external_elo_map: dict[str, float]
    ranked_players_by_team: dict[str, list[dict[str, Any]]]
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
        raw_dark_score = float(payload.get("DarkScore", 0))
        dark_score = _rescale_dark_score(raw_dark_score)
        payload["DarkScore"] = dark_score
        payload["Alert"] = dark_score >= NEW_SCORE_MAX
        upset_pct = int(round(float(payload.get("p_final", 0.0)) * 100.0))
        favorite = str(payload.get("favorite_by_elo", home_team))
        underdog = str(payload.get("underdog_by_elo", away_team))
        risk_band, impact_level = _risk_band(dark_score)
        summary, takeaways = self._fan_takeaways(
            score=dark_score,
            upset_pct=upset_pct,
            favorite_team=favorite,
            underdog_team=underdog,
            elo_home=float(feature_row["elo_home_pre"]),
            elo_away=float(feature_row["elo_away_pre"]),
        )
        payload["risk_band"] = risk_band
        payload["impact_level"] = impact_level
        payload["fan_summary"] = summary
        payload["fan_takeaways"] = takeaways
        dark_knight_bundle = self._resolve_dark_knights(
            home_team=str(payload.get("home_team", home_team)),
            away_team=str(payload.get("away_team", away_team)),
            favorite_team=favorite,
            underdog_team=underdog,
            dark_score=dark_score,
        )
        payload["dark_knight_team"] = dark_knight_bundle["team"]
        payload["dark_knight_rule"] = dark_knight_bundle["rule"]
        payload["dark_knights"] = dark_knight_bundle["players"]
        payload["dark_knight"] = dark_knight_bundle["players"][0]
        return payload

    @staticmethod
    def _player_line(team: str, player: dict[str, Any] | None, fallback: str) -> str:
        if not player:
            return fallback
        name = str(player.get("player_name", "Data missing")) or "Data missing"
        position = str(player.get("position", "Data missing")) or "Data missing"
        skill_score = int(player.get("skill_score", 0) or 0)
        return f"{name} ({team}, {position}, skill {skill_score}) is the main player signal."

    def _fan_takeaways(
        self,
        *,
        score: float,
        upset_pct: int,
        favorite_team: str,
        underdog_team: str,
        elo_home: float,
        elo_away: float,
    ) -> tuple[str, list[str]]:
        favorite_top = self._top_players(favorite_team, 1)
        underdog_top = self._top_players(underdog_team, 2)
        favorite_signal = favorite_top[0] if favorite_top else None
        underdog_signal = underdog_top[0] if underdog_top else None
        underdog_signal_2 = underdog_top[1] if len(underdog_top) > 1 else None
        elo_gap = int(round(abs(elo_home - elo_away)))

        if score <= NEW_SCORE_MIN:
            summary = f"Low range (<={int(NEW_SCORE_MIN)}): {favorite_team} are favored in most simulations ({upset_pct}% upset path)."
            return summary, [
                f"Elo context: {favorite_team} carry about a {elo_gap}-point rating edge pre-match.",
                self._player_line(
                    favorite_team,
                    favorite_signal,
                    f"{favorite_team} control signal unavailable because favorite player data is missing.",
                ),
                f"{underdog_team} likely need a high-impact performance to flip this.",
            ]

        if score < NEW_SCORE_MAX:
            summary = f"Mean range (~{NEW_SCORE_MEAN:.1f}): this matchup is balanced and can swing on one key moment ({upset_pct}% upset path)."
            return summary, [
                f"{favorite_team} are still the safer side, but not by much.",
                self._player_line(
                    underdog_team,
                    underdog_signal,
                    f"{underdog_team} have a realistic route to avoid defeat, but top-player data is missing.",
                ),
                "Treat this as a balanced-risk fixture around the model midpoint.",
            ]

        summary = f"High range (>={int(NEW_SCORE_MAX)}): strong upset pressure ({upset_pct}% upset path) with {underdog_team} fully live."
        player_a = self._player_line(
            underdog_team,
            underdog_signal,
            f"{underdog_team} player-impact data is partially missing.",
        )
        player_b = self._player_line(
            underdog_team,
            underdog_signal_2,
            f"Second underdog contributor data is missing for {underdog_team}.",
        )
        return summary, [
            f"{favorite_team} still carry pedigree, but their edge is fragile here.",
            player_a,
            player_b,
        ]

    @staticmethod
    def _to_knight_payload(team: str, player: dict[str, Any], reason: str) -> dict[str, Any]:
        return {
            "team": team,
            "player_name": str(player.get("player_name", "Data missing")) or "Data missing",
            "position": str(player.get("position", "Data missing")) or "Data missing",
            "skill_score": int(player.get("skill_score", 0) or 0),
            "reason": reason,
        }

    @staticmethod
    def _missing_knight(team: str, reason: str) -> dict[str, Any]:
        return {
            "team": team,
            "player_name": "Data missing",
            "position": "Data missing",
            "skill_score": 0,
            "reason": reason,
        }

    def _top_players(self, team: str, limit: int) -> list[dict[str, Any]]:
        players = self.ranked_players_by_team.get(_slug_key(team), [])
        return list(players[:limit])

    def _resolve_dark_knights(
        self,
        *,
        home_team: str,
        away_team: str,
        favorite_team: str,
        underdog_team: str,
        dark_score: float,
    ) -> dict[str, Any]:
        if dark_score <= NEW_SCORE_MIN:
            team = favorite_team
            need = 1
            rule = f"Low range (<={int(NEW_SCORE_MIN)}): showing the top player from the favorite team."
            reason = "Favorite control driver for this matchup."
        elif dark_score < NEW_SCORE_MAX:
            team = underdog_team
            need = 1
            rule = f"Mean range (~{NEW_SCORE_MEAN:.1f}): showing the top player from the underdog team."
            reason = "Underdog x-factor in a balanced-risk matchup."
        else:
            team = underdog_team
            need = 2
            rule = f"High range (>={int(NEW_SCORE_MAX)}): showing the top two players from the underdog team."
            reason = "Primary underdog contributors driving upset upside."

        selected = self._top_players(team, need)
        knights = [self._to_knight_payload(team, p, reason) for p in selected]

        while len(knights) < need:
            missing_reason = f"{reason} Additional underdog player data is missing."
            knights.append(self._missing_knight(team, missing_reason))

        if not knights:
            knights = [self._missing_knight(team, "Player data missing for this team.")]

        return {"team": team, "rule": rule, "players": knights}

    def _demo_description(self, row: dict[str, Any]) -> tuple[str, list[str]]:
        score = float(row.get("dark_score") or row.get("DarkScore") or 0.0)
        upset_pct = int(round(float(row.get("p_final") or 0.0) * 100))
        favorite = str(row.get("favorite_by_elo") or "Favorite")
        underdog = str(row.get("underdog_by_elo") or "Underdog")
        underdog_top = self._top_players(underdog, 2)
        favorite_top = self._top_players(favorite, 1)

        focus_players: list[str] = []
        if score <= NEW_SCORE_MIN:
            top = favorite_top[0] if favorite_top else None
            description = (
                f"Low range (<={int(NEW_SCORE_MIN)}, {upset_pct}%): {favorite} remain the stable side in this matchup."
            )
            if top:
                focus_players.append(f"{top.get('player_name', 'Data missing')} ({favorite})")
            return description, focus_players

        if score < NEW_SCORE_MAX:
            top = underdog_top[0] if underdog_top else None
            description = (
                f"Mean range (~{NEW_SCORE_MEAN:.1f}, {upset_pct}%): {underdog} have a live path if their top threat delivers."
            )
            if top:
                focus_players.append(f"{top.get('player_name', 'Data missing')} ({underdog})")
            return description, focus_players

        description = f"High range (>={int(NEW_SCORE_MAX)}, {upset_pct}%): {underdog} can realistically disrupt the expected result."
        for item in underdog_top[:2]:
            focus_players.append(f"{item.get('player_name', 'Data missing')} ({underdog})")
        return description, focus_players

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
        for record in records:
            raw_score = float(record.get("dark_score") or record.get("DarkScore") or 0.0)
            scaled_score = _rescale_dark_score(raw_score)
            record["dark_score"] = scaled_score
            record["alert"] = scaled_score >= NEW_SCORE_MAX
            description, focus_players = self._demo_description(record)
            record["description"] = description
            record["focus_players"] = focus_players
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
        ranked_players_by_team = _load_ranked_players_by_team(_FC26_PLAYERS_PATH)
        return ModelService(
            xgb_model=xgb_model,
            calibrator=calibrator,
            feature_info=feature_info,
            fc_team=fc_team,
            external_elo_map=external_elo_map,
            ranked_players_by_team=ranked_players_by_team,
            alert_threshold=float(feature_info.get("alert_threshold", 0.60)),
        )
    except Exception as exc:
        logger.warning("ModelService could not be loaded: %s", exc)
        return None
