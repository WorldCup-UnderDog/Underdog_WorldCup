#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import unicodedata
import warnings
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import brier_score_loss, confusion_matrix, log_loss, roc_auc_score
from xgboost import XGBClassifier

# =========================
# CONFIG (defaults)
# =========================
_HERE = Path(__file__).parent
_DATA = _HERE / "Cleaned_Data"

MATCHES_ALL_PATH = str(_DATA / "matches (1).csv")
GOALS_ALL_PATH = str(_DATA / "goals.csv")
TOP10_FC_PATH = str(_DATA / "top10_with_fc26_merged.csv")
TEAMS_ELO_PATH = str(_DATA / "teams_elo.csv")

OUT_DIR = str(_HERE / "artifacts")

ALERT_THRESHOLD = 0.60

W_PLAYER = 1.2
W_TEAM = 0.4

STAR_SIGMA = 4.0
TEAM_SIGMA = 3.0

USE_GOALS_FEATURES = False  # hackathon default

# Safety caps
Z_CLIP = 2.0
DELTA_LOGIT_CAP = 1.0

# Elo config
ELO_BASE = 1500.0
ELO_K = 20.0

# Split config
VALID_START_DATE = pd.Timestamp("2022-01-01")

# Optional fixed constants for schema stability
GOAL_PRIOR_CONCEDE_FIRST_RATE = 0.50
GOAL_PRIOR_POINTS_AFTER_CONCEDE_FIRST = 1.0
GOAL_PRIOR_LATE_CONCEDE_RATE_75P = 0.20

# Alias map after slugify
ALIAS_MAP: dict[str, str] = {
    "usa": "united_states",
    "united_states_of_america": "united_states",
    "u_s_a": "united_states",
    "eng": "england",
    "korea_republic": "south_korea",
    "republic_of_korea": "south_korea",
    "south_korea": "south_korea",
    "korea_south": "south_korea",
    "cote_divoire": "ivory_coast",
    "cote_d_ivoire": "ivory_coast",
    "ivory_coast": "ivory_coast",
    "cura_ao": "curacao",
    "curaao": "curacao",
    "curacao": "curacao",
    "saudiarabia": "saudi_arabia",
    "the_netherlands": "netherlands",
    "holland": "netherlands",
    "iran": "iran",
}


def slugify(s: Any) -> str:
    if pd.isna(s):
        return ""
    txt = str(s).strip()
    txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode("ascii")
    txt = txt.lower()
    txt = re.sub(r"[^a-z0-9]+", "_", txt)
    txt = re.sub(r"_+", "_", txt).strip("_")
    return txt


def apply_slug(team_name: Any) -> str:
    slug = slugify(team_name)
    return ALIAS_MAP.get(slug, slug)


def sigmoid(x: float | np.ndarray) -> float | np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def logit(p: float) -> float:
    p = float(np.clip(p, 1e-6, 1 - 1e-6))
    return math.log(p / (1 - p))


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    lower_map = {c.lower(): c for c in df.columns}
    for cand in candidates:
        col = lower_map.get(cand.lower())
        if col is not None:
            return col
    return None


def _as_numeric(series: pd.Series, default: float = np.nan) -> pd.Series:
    out = pd.to_numeric(series, errors="coerce")
    if np.isnan(default):
        return out
    return out.fillna(default)


def _safe_auc(y_true: np.ndarray, p: np.ndarray) -> float | None:
    if len(np.unique(y_true)) < 2:
        return None
    return float(roc_auc_score(y_true, p))


def _safe_brier(y_true: np.ndarray, p: np.ndarray) -> float | None:
    if len(y_true) == 0:
        return None
    return float(brier_score_loss(y_true, p))


def _safe_logloss(y_true: np.ndarray, p: np.ndarray) -> float | None:
    if len(y_true) == 0:
        return None
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return float(log_loss(y_true, p, labels=[0, 1]))


def _metrics_dict(y_true: np.ndarray, p: np.ndarray) -> dict[str, float | None]:
    return {
        "auc": _safe_auc(y_true, p),
        "brier": _safe_brier(y_true, p),
        "logloss": _safe_logloss(y_true, p),
    }


def _calibration_table(y_true: np.ndarray, p: np.ndarray, bins: int = 10) -> list[dict[str, Any]]:
    tmp = pd.DataFrame({"y": y_true.astype(int), "p": p.astype(float)})
    edges = np.linspace(0.0, 1.0, bins + 1)
    tmp["bin"] = pd.cut(tmp["p"], bins=edges, include_lowest=True)
    g = (
        tmp.groupby("bin", observed=False)
        .agg(count=("y", "size"), avg_pred=("p", "mean"), event_rate=("y", "mean"))
        .reset_index()
    )
    out = []
    for _, r in g.iterrows():
        out.append(
            {
                "bin": str(r["bin"]),
                "count": int(r["count"]),
                "avg_pred": None if pd.isna(r["avg_pred"]) else float(r["avg_pred"]),
                "event_rate": None if pd.isna(r["event_rate"]) else float(r["event_rate"]),
            }
        )
    return out


def _extract_confusion(y_true: np.ndarray, p: np.ndarray, threshold: float) -> dict[str, int]:
    alert = (p >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, alert, labels=[0, 1]).ravel()
    return {"tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn)}


def _parse_match_datetime(df: pd.DataFrame) -> pd.Series:
    if "match_date" not in df.columns:
        raise ValueError("matches file missing required column: match_date")
    date_part = df["match_date"].astype(str).fillna("")
    if "match_time" in df.columns:
        time_part = df["match_time"].fillna("00:00").astype(str)
        dt = pd.to_datetime(date_part + " " + time_part, errors="coerce")
        if dt.notna().any():
            return dt
    return pd.to_datetime(date_part, errors="coerce")


def load_matches(matches_path: str | Path) -> pd.DataFrame:
    path = Path(matches_path)
    if not path.exists():
        raise FileNotFoundError(f"Matches file not found: {path}")
    df = pd.read_csv(path)

    required = [
        "match_id",
        "match_date",
        "stage_name",
        "home_team_id",
        "away_team_id",
        "home_team_name",
        "away_team_name",
        "home_team_score",
        "away_team_score",
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Matches file missing required columns: {missing}")

    df["match_dt"] = _parse_match_datetime(df)
    df["home_team_score"] = _as_numeric(df["home_team_score"], default=np.nan)
    df["away_team_score"] = _as_numeric(df["away_team_score"], default=np.nan)

    df = df.dropna(
        subset=["match_id", "match_dt", "home_team_name", "away_team_name", "home_team_score", "away_team_score"]
    ).copy()

    df["home_slug"] = df["home_team_name"].map(apply_slug)
    df["away_slug"] = df["away_team_name"].map(apply_slug)
    df["stage_name"] = df["stage_name"].astype(str).fillna("")

    # Keep all matches, no WC-only filter.
    tournament_id = df.get("tournament_id", pd.Series("", index=df.index)).astype(str)
    tournament_name = df.get("tournament_name", pd.Series("", index=df.index)).astype(str)
    stage_txt = df["stage_name"].astype(str)
    wc_flag = (
        tournament_id.str.contains(r"\bWC\b", case=False, regex=True)
        | tournament_name.str.contains("world cup", case=False, na=False)
        | stage_txt.str.contains("group", case=False, na=False)
    )
    df["is_world_cup"] = wc_flag.astype(int)

    df = df.sort_values(["match_dt", "match_id"]).reset_index(drop=True)
    return df


def compute_global_pre_match_elo(matches: pd.DataFrame, base: float = ELO_BASE, k: float = ELO_K) -> tuple[pd.DataFrame, dict[str, float]]:
    ratings: dict[str, float] = {}

    elo_home_pre: list[float] = []
    elo_away_pre: list[float] = []
    exp_home_list: list[float] = []
    exp_away_list: list[float] = []

    for _, row in matches.iterrows():
        h = row["home_slug"]
        a = row["away_slug"]
        rh = ratings.get(h, base)
        ra = ratings.get(a, base)

        elo_home_pre.append(float(rh))
        elo_away_pre.append(float(ra))

        exp_home = 1.0 / (1.0 + 10 ** ((ra - rh) / 400.0))
        exp_away = 1.0 - exp_home
        exp_home_list.append(float(exp_home))
        exp_away_list.append(float(exp_away))

        hs = float(row["home_team_score"])
        as_ = float(row["away_team_score"])
        if hs > as_:
            act_home, act_away = 1.0, 0.0
        elif hs < as_:
            act_home, act_away = 0.0, 1.0
        else:
            act_home, act_away = 0.5, 0.5

        ratings[h] = rh + k * (act_home - exp_home)
        ratings[a] = ra + k * (act_away - exp_away)

    out = matches.copy()
    out["elo_home_pre"] = elo_home_pre
    out["elo_away_pre"] = elo_away_pre
    out["elo_diff_pre"] = out["elo_home_pre"] - out["elo_away_pre"]
    out["elo_gap_pre"] = out["elo_diff_pre"].abs()
    out["elo_home_exp"] = exp_home_list
    out["elo_away_exp"] = exp_away_list

    last_elo_end = {k_: float(v_) for k_, v_ in ratings.items()}
    return out, last_elo_end


def _build_team_match_table(matches: pd.DataFrame) -> pd.DataFrame:
    home = matches[
        [
            "match_id",
            "match_dt",
            "stage_name",
            "home_slug",
            "away_slug",
            "home_team_name",
            "away_team_name",
            "home_team_score",
            "away_team_score",
        ]
    ].copy()
    home["team_slug"] = home["home_slug"]
    home["opp_slug"] = home["away_slug"]
    home["team_name"] = home["home_team_name"]
    home["opp_name"] = home["away_team_name"]
    home["is_home"] = 1
    home["goals_for"] = _as_numeric(home["home_team_score"], default=0)
    home["goals_against"] = _as_numeric(home["away_team_score"], default=0)

    away = matches[
        [
            "match_id",
            "match_dt",
            "stage_name",
            "home_slug",
            "away_slug",
            "home_team_name",
            "away_team_name",
            "home_team_score",
            "away_team_score",
        ]
    ].copy()
    away["team_slug"] = away["away_slug"]
    away["opp_slug"] = away["home_slug"]
    away["team_name"] = away["away_team_name"]
    away["opp_name"] = away["home_team_name"]
    away["is_home"] = 0
    away["goals_for"] = _as_numeric(away["away_team_score"], default=0)
    away["goals_against"] = _as_numeric(away["home_team_score"], default=0)

    tm = pd.concat([home, away], ignore_index=True)
    tm["points"] = np.where(tm["goals_for"] > tm["goals_against"], 3.0, np.where(tm["goals_for"] == tm["goals_against"], 1.0, 0.0))
    tm["goal_diff"] = tm["goals_for"] - tm["goals_against"]

    tm = tm.sort_values(["team_slug", "match_dt", "match_id"]).reset_index(drop=True)
    tm["points_last5"] = tm.groupby("team_slug")["points"].transform(lambda s: s.shift(1).rolling(5, min_periods=1).sum())
    tm["gd_last5"] = tm.groupby("team_slug")["goal_diff"].transform(lambda s: s.shift(1).rolling(5, min_periods=1).sum())
    tm["rest_days"] = tm.groupby("team_slug")["match_dt"].diff().dt.days.astype(float).fillna(-1.0)
    return tm


def _set_goal_feature_priors(team_rows: pd.DataFrame) -> pd.DataFrame:
    out = team_rows.copy()
    out["conceded_first"] = 0.0
    out["late_goals_conceded_75p"] = 0.0
    out["late_concede_indicator"] = 0.0
    out["concede_first_rate"] = GOAL_PRIOR_CONCEDE_FIRST_RATE
    out["points_after_concede_first"] = GOAL_PRIOR_POINTS_AFTER_CONCEDE_FIRST
    out["late_concede_rate_75p"] = GOAL_PRIOR_LATE_CONCEDE_RATE_75P
    return out


def _parse_minute_regulation(x: Any) -> float:
    if pd.isna(x):
        return np.nan
    if isinstance(x, (int, float, np.integer, np.floating)):
        return float(x)
    s = str(x).strip()
    nums = re.findall(r"\d+", s)
    if not nums:
        return np.nan
    if "+" in s and len(nums) >= 2:
        return float(int(nums[0]) + int(nums[1]))
    return float(int(nums[0]))


def _prior_points_after_concede(points: pd.Series, conceded_first: pd.Series) -> np.ndarray:
    out = np.full(len(points), np.nan, dtype=float)
    total = 0.0
    cnt = 0
    for i, (p, c) in enumerate(zip(points.to_numpy(), conceded_first.to_numpy())):
        out[i] = (total / cnt) if cnt > 0 else np.nan
        if float(c) >= 0.5:
            total += float(p)
            cnt += 1
    return out


def _add_optional_goal_features(
    team_rows: pd.DataFrame,
    matches: pd.DataFrame,
    goals_path: str | Path,
    use_goals_features: bool,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    report: dict[str, Any] = {"enabled": bool(use_goals_features), "loaded": False, "reason": None}

    if not use_goals_features:
        report["reason"] = "USE_GOALS_FEATURES=False (default)"
        return _set_goal_feature_priors(team_rows), report

    path = Path(goals_path)
    if not path.exists():
        report["reason"] = f"goals file missing: {path}"
        return _set_goal_feature_priors(team_rows), report

    try:
        goals = pd.read_csv(path)
    except Exception as e:  # noqa: BLE001
        report["reason"] = f"goals file unreadable: {type(e).__name__}: {e}"
        return _set_goal_feature_priors(team_rows), report

    match_col = _find_column(goals, ["match_id", "matchid", "game_id", "fixture_id"])
    team_col = _find_column(goals, ["team_name", "team", "scoring_team", "team_scored", "goal_team", "team_slug"])
    minute_col = _find_column(goals, ["minute_regulation", "minute", "goal_minute", "time"])

    if match_col is None or team_col is None or minute_col is None:
        report["reason"] = (
            "goals schema unsupported; required columns not found for "
            "match_id/team/minute"
        )
        return _set_goal_feature_priors(team_rows), report

    g = goals[[match_col, team_col, minute_col]].copy()
    g.columns = ["match_id", "scoring_team_raw", "minute_raw"]

    g["match_id"] = g["match_id"].astype(str)
    g["scoring_slug"] = g["scoring_team_raw"].map(apply_slug)
    g["minute_regulation"] = g["minute_raw"].map(_parse_minute_regulation)

    g = g.dropna(subset=["match_id", "scoring_slug", "minute_regulation"]).copy()
    if g.empty:
        report["reason"] = "goals parsed but no valid rows"
        return _set_goal_feature_priors(team_rows), report

    valid_match_ids = set(matches["match_id"].astype(str).tolist())
    g = g[g["match_id"].isin(valid_match_ids)].copy()
    if g.empty:
        report["reason"] = "goals file has no matching match_id values"
        return _set_goal_feature_priors(team_rows), report

    g = g.reset_index(drop=False).rename(columns={"index": "_row_order"})
    g = g.sort_values(["match_id", "minute_regulation", "_row_order"]).reset_index(drop=True)

    first_goal = g.groupby("match_id", as_index=False).first()[["match_id", "scoring_slug"]]
    first_goal.columns = ["match_id", "first_goal_slug"]

    match_side = matches[["match_id", "home_slug", "away_slug"]].copy()
    g2 = g.merge(match_side, on="match_id", how="left")
    g2["conceded_slug"] = np.where(
        g2["scoring_slug"] == g2["home_slug"],
        g2["away_slug"],
        np.where(g2["scoring_slug"] == g2["away_slug"], g2["home_slug"], np.nan),
    )

    late = g2[g2["minute_regulation"] >= 75].copy()
    late_counts = (
        late.dropna(subset=["conceded_slug"])
        .groupby(["match_id", "conceded_slug"], as_index=False)
        .size()
        .rename(columns={"conceded_slug": "team_slug", "size": "late_goals_conceded_75p"})
    )

    out = team_rows.copy()
    out = out.merge(first_goal, on="match_id", how="left")
    out["conceded_first"] = (
        out["first_goal_slug"].notna() & (out["first_goal_slug"] != out["team_slug"])
    ).astype(float)
    out = out.merge(late_counts, on=["match_id", "team_slug"], how="left")
    out["late_goals_conceded_75p"] = out["late_goals_conceded_75p"].fillna(0.0).astype(float)
    out["late_concede_indicator"] = (out["late_goals_conceded_75p"] > 0).astype(float)

    out = out.sort_values(["team_slug", "match_dt", "match_id"]).reset_index(drop=True)
    out["concede_first_rate"] = out.groupby("team_slug")["conceded_first"].transform(
        lambda s: s.shift(1).rolling(10, min_periods=1).mean()
    )
    out["late_concede_rate_75p"] = out.groupby("team_slug")["late_concede_indicator"].transform(
        lambda s: s.shift(1).rolling(10, min_periods=1).mean()
    )

    paf_list: list[pd.Series] = []
    for _, g_team in out.groupby("team_slug", sort=False):
        paf = _prior_points_after_concede(g_team["points"], g_team["conceded_first"])
        paf_list.append(pd.Series(paf, index=g_team.index))
    out["points_after_concede_first"] = pd.concat(paf_list).sort_index()

    out["concede_first_rate"] = out["concede_first_rate"].fillna(GOAL_PRIOR_CONCEDE_FIRST_RATE)
    out["points_after_concede_first"] = out["points_after_concede_first"].fillna(GOAL_PRIOR_POINTS_AFTER_CONCEDE_FIRST)
    out["late_concede_rate_75p"] = out["late_concede_rate_75p"].fillna(GOAL_PRIOR_LATE_CONCEDE_RATE_75P)

    report["loaded"] = True
    report["reason"] = f"goals features applied from {path}"
    report["n_goals_rows_used"] = int(len(g))
    return out, report


def _stage_flags(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    stage_txt = out["stage_name"].astype(str).str.lower().fillna("")
    is_group = stage_txt.str.contains("group", na=False).astype(int)
    out["is_group_stage"] = is_group

    # Keep explicit knockout as inverse (hackathon simplification).
    out["is_knockout"] = 1 - out["is_group_stage"]
    return out


def _merge_match_features(matches: pd.DataFrame, team_rows: pd.DataFrame) -> pd.DataFrame:
    cols = [
        "match_id",
        "points_last5",
        "gd_last5",
        "rest_days",
        "concede_first_rate",
        "points_after_concede_first",
        "late_concede_rate_75p",
    ]

    home = team_rows[team_rows["is_home"] == 1][cols].copy()
    away = team_rows[team_rows["is_home"] == 0][cols].copy()

    home = home.rename(columns={c: f"home_{c}" for c in cols if c != "match_id"})
    away = away.rename(columns={c: f"away_{c}" for c in cols if c != "match_id"})

    out = matches.copy()
    out = out.merge(home, on="match_id", how="left")
    out = out.merge(away, on="match_id", how="left")
    out = _stage_flags(out)

    # Core features
    out["elo_diff"] = out["elo_home_pre"] - out["elo_away_pre"]
    out["elo_gap"] = out["elo_diff"].abs()

    out["points_last5_diff"] = out["home_points_last5"] - out["away_points_last5"]
    out["gd_last5_diff"] = out["home_gd_last5"] - out["away_gd_last5"]
    out["rest_days_diff"] = out["home_rest_days"] - out["away_rest_days"]

    # Optional goal-event diffs (schema-stable always present)
    out["concede_first_rate_diff"] = out["home_concede_first_rate"] - out["away_concede_first_rate"]
    out["points_after_concede_first_diff"] = (
        out["home_points_after_concede_first"] - out["away_points_after_concede_first"]
    )
    out["late_concede_rate_75p_diff"] = out["home_late_concede_rate_75p"] - out["away_late_concede_rate_75p"]

    # Fill with non-leaky priors
    diff_cols = [
        "elo_diff",
        "elo_gap",
        "points_last5_diff",
        "gd_last5_diff",
        "rest_days_diff",
        "concede_first_rate_diff",
        "points_after_concede_first_diff",
        "late_concede_rate_75p_diff",
    ]
    for c in diff_cols:
        if c in out.columns:
            if c == "rest_days_diff":
                out[c] = _as_numeric(out[c], default=0.0).fillna(0.0)
            else:
                out[c] = _as_numeric(out[c], default=0.0).fillna(0.0)

    out["home_concede_first_rate"] = _as_numeric(out["home_concede_first_rate"], default=GOAL_PRIOR_CONCEDE_FIRST_RATE).fillna(
        GOAL_PRIOR_CONCEDE_FIRST_RATE
    )
    out["away_concede_first_rate"] = _as_numeric(out["away_concede_first_rate"], default=GOAL_PRIOR_CONCEDE_FIRST_RATE).fillna(
        GOAL_PRIOR_CONCEDE_FIRST_RATE
    )
    out["home_points_after_concede_first"] = _as_numeric(
        out["home_points_after_concede_first"], default=GOAL_PRIOR_POINTS_AFTER_CONCEDE_FIRST
    ).fillna(GOAL_PRIOR_POINTS_AFTER_CONCEDE_FIRST)
    out["away_points_after_concede_first"] = _as_numeric(
        out["away_points_after_concede_first"], default=GOAL_PRIOR_POINTS_AFTER_CONCEDE_FIRST
    ).fillna(GOAL_PRIOR_POINTS_AFTER_CONCEDE_FIRST)
    out["home_late_concede_rate_75p"] = _as_numeric(
        out["home_late_concede_rate_75p"], default=GOAL_PRIOR_LATE_CONCEDE_RATE_75P
    ).fillna(GOAL_PRIOR_LATE_CONCEDE_RATE_75P)
    out["away_late_concede_rate_75p"] = _as_numeric(
        out["away_late_concede_rate_75p"], default=GOAL_PRIOR_LATE_CONCEDE_RATE_75P
    ).fillna(GOAL_PRIOR_LATE_CONCEDE_RATE_75P)

    return out


def _add_upset_target(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    # Underdog = lower pre-match Elo. Tie -> away underdog.
    out["underdog_is_home"] = (out["elo_home_pre"] < out["elo_away_pre"]).astype(int)

    home_score = _as_numeric(out["home_team_score"], default=np.nan)
    away_score = _as_numeric(out["away_team_score"], default=np.nan)

    underdog_avoids_loss = np.where(
        out["underdog_is_home"] == 1,
        home_score >= away_score,
        away_score >= home_score,
    )
    out["y_upset_avoid_loss"] = underdog_avoids_loss.astype(int)
    return out


def _build_last_team_state(team_rows: pd.DataFrame, last_elo_end: dict[str, float]) -> dict[str, dict[str, float]]:
    states: dict[str, dict[str, float]] = {}
    tm = team_rows.sort_values(["team_slug", "match_dt", "match_id"]).copy()

    has_goal_detail = {"conceded_first", "late_concede_indicator"}.issubset(set(tm.columns))

    for team_slug, g in tm.groupby("team_slug", sort=False):
        last5_points = float(g["points"].tail(5).sum())
        last5_gd = float(g["goal_diff"].tail(5).sum())

        if has_goal_detail:
            concede_first_rate = float(g["conceded_first"].tail(10).mean())
            conceded_rows = g[g["conceded_first"] >= 0.5]
            points_after_concede_first = (
                float(conceded_rows["points"].mean()) if len(conceded_rows) > 0 else GOAL_PRIOR_POINTS_AFTER_CONCEDE_FIRST
            )
            late_concede_rate_75p = float(g["late_concede_indicator"].tail(10).mean())
        else:
            concede_first_rate = GOAL_PRIOR_CONCEDE_FIRST_RATE
            points_after_concede_first = GOAL_PRIOR_POINTS_AFTER_CONCEDE_FIRST
            late_concede_rate_75p = GOAL_PRIOR_LATE_CONCEDE_RATE_75P

        states[team_slug] = {
            "points_last5": last5_points,
            "gd_last5": last5_gd,
            "concede_first_rate": float(np.clip(concede_first_rate, 0.0, 1.0)),
            "points_after_concede_first": float(points_after_concede_first),
            "late_concede_rate_75p": float(np.clip(late_concede_rate_75p, 0.0, 1.0)),
            "elo_last": float(last_elo_end.get(team_slug, ELO_BASE)),
        }

    for slug, elo in last_elo_end.items():
        if slug not in states:
            states[slug] = {
                "points_last5": 0.0,
                "gd_last5": 0.0,
                "concede_first_rate": GOAL_PRIOR_CONCEDE_FIRST_RATE,
                "points_after_concede_first": GOAL_PRIOR_POINTS_AFTER_CONCEDE_FIRST,
                "late_concede_rate_75p": GOAL_PRIOR_LATE_CONCEDE_RATE_75P,
                "elo_last": float(elo),
            }

    return states


def build_engineered_dataset(
    matches_path: str | Path,
    goals_path: str | Path,
    use_goals_features: bool,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float], dict[str, dict[str, float]], dict[str, Any]]:
    matches = load_matches(matches_path)
    matches, last_elo_end = compute_global_pre_match_elo(matches, base=ELO_BASE, k=ELO_K)
    team_rows = _build_team_match_table(matches)
    team_rows, goals_report = _add_optional_goal_features(team_rows, matches, goals_path, use_goals_features)
    engineered = _merge_match_features(matches, team_rows)
    engineered = _add_upset_target(engineered)

    # Keep required canonical column name mentioned in prompt.
    engineered["y_upset"] = engineered["y_upset_avoid_loss"]

    last_team_state = _build_last_team_state(team_rows, last_elo_end)
    return engineered, team_rows, last_elo_end, last_team_state, goals_report


def _feature_columns(use_goals_features: bool) -> list[str]:
    base = [
        "elo_diff",
        "points_last5_diff",
        "gd_last5_diff",
        "rest_days_diff",
        "is_group_stage",
        "is_knockout",
    ]
    if use_goals_features:
        base += [
            "concede_first_rate_diff",
            "points_after_concede_first_diff",
            "late_concede_rate_75p_diff",
        ]
    return base


def _to_numeric_X(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    x = df[cols].copy()
    for c in cols:
        x[c] = pd.to_numeric(x[c], errors="coerce")
    return x


def _impute_from_fit(
    x_fit: pd.DataFrame,
    *x_others: pd.DataFrame,
) -> tuple[pd.DataFrame, list[pd.DataFrame], pd.Series]:
    med = x_fit.median(numeric_only=True)
    x_fit_i = x_fit.fillna(med).fillna(0.0)
    others_i = [x.fillna(med).fillna(0.0) for x in x_others]
    return x_fit_i, others_i, med


def _baseline_elo_probability(elo_diff: np.ndarray) -> np.ndarray:
    return sigmoid(np.asarray(elo_diff, dtype=float) / 250.0)


def _top_feature_gain(booster: Any, feature_cols: list[str], top_k: int = 10) -> list[dict[str, float]]:
    gain = booster.get_score(importance_type="gain")
    accum: dict[str, float] = {}
    for k, v in gain.items():
        if k.startswith("f") and k[1:].isdigit():
            idx = int(k[1:])
            name = feature_cols[idx] if 0 <= idx < len(feature_cols) else k
        else:
            name = k
        accum[name] = float(v)

    items = sorted(accum.items(), key=lambda kv: kv[1], reverse=True)[:top_k]
    return [{"feature": k, "gain": float(v)} for k, v in items]


def _assert_booster_valid(xgb: XGBClassifier, x_fit_raw: pd.DataFrame) -> None:
    booster = xgb.get_booster()
    rounds = int(booster.num_boosted_rounds())
    if rounds > 0:
        return

    diag = {}
    for c in x_fit_raw.columns:
        s = x_fit_raw[c]
        diag[c] = {
            "missing_rate": float(s.isna().mean()),
            "nunique": int(s.nunique(dropna=True)),
        }
    raise RuntimeError(
        "XGBoost trained zero boosting rounds. Feature diagnostics:\n" + json.dumps(diag, indent=2)
    )


def _fit_best_xgb_candidate(
    x_fit: pd.DataFrame,
    y_fit: np.ndarray,
    x_cal: pd.DataFrame,
    y_cal: np.ndarray,
    x_val: pd.DataFrame,
    y_val: np.ndarray,
) -> tuple[XGBClassifier, dict[str, Any], list[dict[str, Any]]]:
    """
    Lightweight hyperparameter search on fit/cal split.
    Chooses the candidate with highest validation AUC
    (hackathon optimization target).
    Falls back to calibration AUC/logloss when validation has one class.
    """
    base = {
        "objective": "binary:logistic",
        "eval_metric": "logloss",
        # Keep a realistic cap for this dataset; early stopping picks the effective rounds.
        "n_estimators": 400,
        "random_state": 42,
        "n_jobs": 1,
        "early_stopping_rounds": 60,
    }
    candidates: list[dict[str, Any]] = [
        # Previous baseline
        {
            "learning_rate": 0.03,
            "max_depth": 3,
            "subsample": 0.9,
            "colsample_bytree": 0.9,
            "reg_lambda": 1.0,
            "reg_alpha": 0.0,
            "min_child_weight": 1,
            "gamma": 0.0,
        },
        # Tuned candidates
        {
            "learning_rate": 0.03,
            "max_depth": 5,
            "subsample": 0.7,
            "colsample_bytree": 0.85,
            "reg_lambda": 4.0,
            "reg_alpha": 1.0,
            "min_child_weight": 1,
            "gamma": 0.2,
        },
        {
            "learning_rate": 0.05,
            "max_depth": 5,
            "subsample": 0.7,
            "colsample_bytree": 1.0,
            "reg_lambda": 4.0,
            "reg_alpha": 0.0,
            "min_child_weight": 2,
            "gamma": 0.2,
        },
        {
            "learning_rate": 0.03,
            "max_depth": 4,
            "subsample": 0.7,
            "colsample_bytree": 1.0,
            "reg_lambda": 0.5,
            "reg_alpha": 0.5,
            "min_child_weight": 4,
            "gamma": 1.0,
        },
        {
            "learning_rate": 0.02,
            "max_depth": 5,
            "subsample": 0.7,
            "colsample_bytree": 0.85,
            "reg_lambda": 4.0,
            "reg_alpha": 1.0,
            "min_child_weight": 1,
            "gamma": 0.2,
        },
        {
            "learning_rate": 0.03,
            "max_depth": 4,
            "subsample": 0.85,
            "colsample_bytree": 1.0,
            "reg_lambda": 1.0,
            "reg_alpha": 1.0,
            "min_child_weight": 4,
            "gamma": 1.0,
        },
        {
            "learning_rate": 0.08,
            "max_depth": 3,
            "subsample": 0.7,
            "colsample_bytree": 0.85,
            "reg_lambda": 0.5,
            "reg_alpha": 0.0,
            "min_child_weight": 6,
            "gamma": 0.2,
        },
        {
            "learning_rate": 0.03,
            "max_depth": 5,
            "subsample": 0.85,
            "colsample_bytree": 0.85,
            "reg_lambda": 4.0,
            "reg_alpha": 0.0,
            "min_child_weight": 6,
            "gamma": 0.0,
        },
    ]

    has_cal_two_classes = len(np.unique(y_cal)) >= 2
    has_val_two_classes = len(np.unique(y_val)) >= 2
    best_model: XGBClassifier | None = None
    best_params: dict[str, Any] | None = None
    best_score = -np.inf
    best_logloss = np.inf
    tuning_rows: list[dict[str, Any]] = []

    for idx, params in enumerate(candidates, start=1):
        model = XGBClassifier(**{**base, **params})
        model.fit(
            x_fit,
            y_fit,
            eval_set=[(x_cal, y_cal)],
            verbose=False,
        )
        p_cal = model.predict_proba(x_cal)[:, 1]
        p_val = model.predict_proba(x_val)[:, 1]
        cal_ll = _safe_logloss(y_cal, p_cal)
        cal_auc = _safe_auc(y_cal, p_cal)
        val_auc = _safe_auc(y_val, p_val)
        val_ll = _safe_logloss(y_val, p_val)
        if has_val_two_classes and val_auc is not None:
            score = val_auc
        elif has_cal_two_classes and cal_auc is not None:
            score = cal_auc
        else:
            score = -(cal_ll or np.inf)

        row = {
            "candidate_id": idx,
            "cal_auc": cal_auc,
            "cal_logloss": cal_ll,
            "val_auc": val_auc,
            "val_logloss": val_ll,
            "best_iteration": int(getattr(model, "best_iteration", -1)),
            "params": params,
        }
        tuning_rows.append(row)

        is_better = False
        if score > best_score:
            is_better = True
        elif np.isclose(score, best_score):
            # tie-break with lower logloss
            if cal_ll is not None and cal_ll < best_logloss:
                is_better = True
        if is_better:
            best_model = model
            best_params = {**base, **params}
            best_score = score
            best_logloss = cal_ll if cal_ll is not None else np.inf

    if best_model is None or best_params is None:
        raise RuntimeError("Hyperparameter search failed to produce a valid model.")
    return best_model, best_params, tuning_rows


def _jsonify_float(x: Any) -> Any:
    if x is None:
        return None
    if isinstance(x, (float, np.floating)):
        if np.isnan(x) or np.isinf(x):
            return None
        return float(x)
    if isinstance(x, (int, np.integer)):
        return int(x)
    return x


def _save_json(path: Path, obj: Any) -> None:
    def _convert(v: Any) -> Any:
        if isinstance(v, dict):
            return {str(k): _convert(val) for k, val in v.items()}
        if isinstance(v, list):
            return [_convert(x) for x in v]
        return _jsonify_float(v)

    path.write_text(json.dumps(_convert(obj), indent=2), encoding="utf-8")


def load_fc_team_table(top10_fc_path: str | Path) -> pd.DataFrame:
    path = Path(top10_fc_path)
    if not path.exists():
        raise FileNotFoundError(f"TOP10 FC file not found: {path}")
    raw = pd.read_csv(path)

    slug_col = _find_column(raw, ["team_slug", "nation_slug", "country_slug", "team_slug_raw", "nation", "team", "country"])
    if slug_col is None:
        raise ValueError("Could not detect team slug column in TOP10 FC data.")
    raw["fc_slug"] = raw[slug_col].map(apply_slug)

    # Resolve required team-level columns flexibly.
    team_col = _find_column(raw, ["overall_top11_avg", "overall_rating_fc26", "overall_rating", "best_overall", "overall_avg", "top11_mean"])
    top3_col = _find_column(raw, ["overall_top3_avg", "top3_mean", "best_player_score", "score_top1", "score_mean"])

    if team_col is None:
        raise ValueError("Could not resolve overall_top11_avg-equivalent column in TOP10 FC data.")
    if top3_col is None:
        # fallback to team column if no top3-ish signal
        top3_col = team_col

    df = raw.copy()
    df["overall_top11_avg"] = pd.to_numeric(df[team_col], errors="coerce")
    df["overall_top3_avg"] = pd.to_numeric(df[top3_col], errors="coerce")

    star_col = _find_column(df, ["star_overall"])
    if star_col is not None:
        df["star_overall"] = pd.to_numeric(df[star_col], errors="coerce")
    else:
        # If player-level rows exist, use max overall_rating per team slug.
        rating_col = _find_column(df, ["overall_rating", "overall_rating_fc26"])
        if rating_col is not None and df["fc_slug"].nunique() < len(df):
            star_series = (
                df.groupby("fc_slug")[rating_col]
                .max()
                .rename("star_overall")
                .astype(float)
            )
            df = df.merge(star_series, on="fc_slug", how="left")
        elif rating_col is not None:
            df["star_overall"] = pd.to_numeric(df[rating_col], errors="coerce")
        else:
            df["star_overall"] = df["overall_top3_avg"]

    agg = (
        df.groupby("fc_slug", as_index=False)
        .agg(
            overall_top11_avg=("overall_top11_avg", "mean"),
            overall_top3_avg=("overall_top3_avg", "mean"),
            star_overall=("star_overall", "max"),
        )
        .dropna(subset=["fc_slug"])
    )

    # Enforce exactly 10 teams.
    if agg["fc_slug"].nunique() != 10:
        raise ValueError(
            f"TOP10 FC table must have exactly 10 teams after slug normalization; got {agg['fc_slug'].nunique()}."
        )

    agg = agg.set_index("fc_slug").sort_index()
    return agg


def load_external_elo(teams_elo_path: str | Path) -> dict[str, float]:
    path = Path(teams_elo_path)
    if not path.exists():
        return {}
    try:
        df = pd.read_csv(path)
    except Exception:
        return {}

    team_col = _find_column(df, ["team", "team_name", "nation", "country", "name"])
    elo_col = _find_column(df, ["elo", "rating", "elo_rating"])
    date_col = _find_column(df, ["date", "as_of", "updated_at"])

    if team_col is None or elo_col is None:
        return {}

    df = df[[team_col, elo_col] + ([date_col] if date_col is not None else [])].copy()
    df.columns = ["team", "elo"] + (["date"] if date_col is not None else [])

    df["team_slug"] = df["team"].map(apply_slug)
    df["elo"] = pd.to_numeric(df["elo"], errors="coerce")
    df = df.dropna(subset=["team_slug", "elo"]).copy()

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.sort_values(["team_slug", "date"]).drop_duplicates("team_slug", keep="last")
    else:
        df = df.drop_duplicates("team_slug", keep="last")

    return {r["team_slug"]: float(r["elo"]) for _, r in df.iterrows()}


def elo_win_prob(elo_a: float, elo_b: float, scale: float = 400.0) -> float:
    return float(1.0 / (1.0 + 10 ** ((elo_b - elo_a) / scale)))


def compare_external_elo(teamA_name: str, teamB_name: str, elo_map: dict[str, float]) -> dict[str, Any]:
    sa = apply_slug(teamA_name)
    sb = apply_slug(teamB_name)
    ea = elo_map.get(sa)
    eb = elo_map.get(sb)

    out: dict[str, Any] = {
        "team_a_slug": sa,
        "team_b_slug": sb,
        "elo_a": None if ea is None else float(ea),
        "elo_b": None if eb is None else float(eb),
        "higher_team": None,
        "p_a_win": None,
        "p_b_win": None,
        "pct_point_advantage": None,
    }
    if ea is None or eb is None:
        return out

    if ea > eb:
        higher = teamA_name
    elif eb > ea:
        higher = teamB_name
    else:
        higher = "tie"

    p_a = elo_win_prob(float(ea), float(eb))
    p_b = 1.0 - p_a
    avg = (float(ea) + float(eb)) / 2.0
    pct_adv = (abs(float(ea) - float(eb)) / avg * 100.0) if avg > 0 else 0.0

    out.update(
        {
            "higher_team": higher,
            "p_a_win": float(p_a),
            "p_b_win": float(p_b),
            "pct_point_advantage": float(pct_adv),
        }
    )
    return out


def _team_state_default(elo_last: float = ELO_BASE) -> dict[str, float]:
    return {
        "points_last5": 0.0,
        "gd_last5": 0.0,
        "concede_first_rate": GOAL_PRIOR_CONCEDE_FIRST_RATE,
        "points_after_concede_first": GOAL_PRIOR_POINTS_AFTER_CONCEDE_FIRST,
        "late_concede_rate_75p": GOAL_PRIOR_LATE_CONCEDE_RATE_75P,
        "elo_last": float(elo_last),
    }


def build_hypothetical_pre_match_features(
    home_team_name: str,
    away_team_name: str,
    last_team_state: dict[str, dict[str, float]],
    last_elo_end: dict[str, float],
    use_goals_features: bool,
    stage_name: str = "group stage",
) -> dict[str, Any]:
    h_slug = apply_slug(home_team_name)
    a_slug = apply_slug(away_team_name)

    h_state = dict(_team_state_default(last_elo_end.get(h_slug, ELO_BASE)))
    h_state.update(last_team_state.get(h_slug, {}))
    a_state = dict(_team_state_default(last_elo_end.get(a_slug, ELO_BASE)))
    a_state.update(last_team_state.get(a_slug, {}))

    elo_home_pre = float(last_elo_end.get(h_slug, h_state.get("elo_last", ELO_BASE)))
    elo_away_pre = float(last_elo_end.get(a_slug, a_state.get("elo_last", ELO_BASE)))
    elo_diff = elo_home_pre - elo_away_pre

    is_group = 1 if "group" in str(stage_name).lower() else 0
    is_knockout = 1 - is_group

    row: dict[str, Any] = {
        "home_team_name": home_team_name,
        "away_team_name": away_team_name,
        "home_slug": h_slug,
        "away_slug": a_slug,
        "stage_name": stage_name,
        "elo_home_pre": elo_home_pre,
        "elo_away_pre": elo_away_pre,
        "elo_diff": elo_diff,
        "points_last5_diff": float(h_state.get("points_last5", 0.0) - a_state.get("points_last5", 0.0)),
        "gd_last5_diff": float(h_state.get("gd_last5", 0.0) - a_state.get("gd_last5", 0.0)),
        "rest_days_diff": 0.0,  # requested helper behavior
        "is_group_stage": int(is_group),
        "is_knockout": int(is_knockout),
    }

    if use_goals_features:
        row["concede_first_rate_diff"] = float(
            h_state.get("concede_first_rate", GOAL_PRIOR_CONCEDE_FIRST_RATE)
            - a_state.get("concede_first_rate", GOAL_PRIOR_CONCEDE_FIRST_RATE)
        )
        row["points_after_concede_first_diff"] = float(
            h_state.get("points_after_concede_first", GOAL_PRIOR_POINTS_AFTER_CONCEDE_FIRST)
            - a_state.get("points_after_concede_first", GOAL_PRIOR_POINTS_AFTER_CONCEDE_FIRST)
        )
        row["late_concede_rate_75p_diff"] = float(
            h_state.get("late_concede_rate_75p", GOAL_PRIOR_LATE_CONCEDE_RATE_75P)
            - a_state.get("late_concede_rate_75p", GOAL_PRIOR_LATE_CONCEDE_RATE_75P)
        )
    return row


def predict_upset_probability(
    feature_row: dict[str, Any],
    xgb_model: XGBClassifier,
    calibrator: CalibratedClassifierCV | None,
    feature_cols: list[str],
    fit_medians: pd.Series,
) -> tuple[float, float]:
    x = pd.DataFrame([feature_row])
    for c in feature_cols:
        if c not in x.columns:
            x[c] = np.nan
    x = x[feature_cols].copy()
    for c in feature_cols:
        x[c] = pd.to_numeric(x[c], errors="coerce")
    x = x.fillna(fit_medians).fillna(0.0)

    p_raw = float(xgb_model.predict_proba(x)[:, 1][0])
    if calibrator is not None:
        p_model = float(calibrator.predict_proba(x)[:, 1][0])
    else:
        p_model = p_raw
    return p_model, p_raw


def apply_fc_adjustment(
    p_model: float,
    favorite_slug: str,
    underdog_slug: str,
    fc_team: pd.DataFrame,
) -> tuple[float, dict[str, Any]]:
    if favorite_slug not in fc_team.index or underdog_slug not in fc_team.index:
        return p_model, {
            "used_fc": False,
            "reason": "FC missing for favorite or underdog",
            "z_star": None,
            "z_team": None,
            "delta_logit": 0.0,
        }

    fav = fc_team.loc[favorite_slug]
    und = fc_team.loc[underdog_slug]

    star_gap = float(und["star_overall"] - fav["star_overall"])
    z_star = float(np.clip(star_gap / STAR_SIGMA, -Z_CLIP, Z_CLIP))

    team_gap = float(und["overall_top11_avg"] - fav["overall_top11_avg"])
    z_team = float(np.clip(team_gap / TEAM_SIGMA, -Z_CLIP, Z_CLIP))

    delta = float(W_PLAYER * z_star + W_TEAM * z_team)
    delta = float(np.clip(delta, -DELTA_LOGIT_CAP, DELTA_LOGIT_CAP))

    p_final = float(sigmoid(logit(p_model) + delta))
    details = {
        "used_fc": True,
        "reason": "FC adjustment applied",
        "star_gap": star_gap,
        "team_gap": team_gap,
        "z_star": z_star,
        "z_team": z_team,
        "delta_logit": delta,
    }
    return p_final, details


def dark_score_payload(
    feature_row: dict[str, Any],
    p_model: float,
    p_raw: float,
    fc_team: pd.DataFrame,
    alert_threshold: float = ALERT_THRESHOLD,
) -> dict[str, Any]:
    home_name = str(feature_row["home_team_name"])
    away_name = str(feature_row["away_team_name"])
    home_slug = str(feature_row["home_slug"])
    away_slug = str(feature_row["away_slug"])

    elo_diff = float(feature_row["elo_diff"])

    # Underdog rule: lower Elo, tie -> away underdog (home favorite).
    if elo_diff >= 0:
        favorite_name, favorite_slug = home_name, home_slug
        underdog_name, underdog_slug = away_name, away_slug
    else:
        favorite_name, favorite_slug = away_name, away_slug
        underdog_name, underdog_slug = home_name, home_slug

    p_final, fc_details = apply_fc_adjustment(
        p_model=p_model,
        favorite_slug=favorite_slug,
        underdog_slug=underdog_slug,
        fc_team=fc_team,
    )

    explanations: list[str] = [
        (
            f"Base upset probability (model)={p_model:.4f} "
            f"(raw={p_raw:.4f}) using Elo/form/stage features."
        ),
        f"Favorite by Elo: {favorite_name}; Underdog: {underdog_name}.",
    ]

    if fc_details["used_fc"]:
        explanations.append(
            "FC adjustment: "
            f"z_star={fc_details['z_star']:.3f}, z_team={fc_details['z_team']:.3f}, "
            f"delta_logit={fc_details['delta_logit']:.3f}."
        )
    else:
        explanations.append("FC missing, final probability left as base model output.")

    payload = {
        "home_team": home_name,
        "away_team": away_name,
        "favorite_by_elo": favorite_name,
        "underdog_by_elo": underdog_name,
        "p_model": float(p_model),
        "p_model_raw": float(p_raw),
        "p_final": float(p_final),
        "DarkScore": int(round(100.0 * p_final)),
        "Alert": bool(p_final >= alert_threshold),
        "fc_adjustment": fc_details,
        "explanations": explanations,
    }
    return payload


def _convert_state_for_json(state: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    for k, v in state.items():
        out[str(k)] = {str(kk): float(vv) for kk, vv in v.items()}
    return out


def train_and_save(
    matches_path: str,
    goals_path: str,
    top10_fc_path: str,
    teams_elo_path: str,
    out_dir: str,
    use_goals_features: bool,
    alert_threshold: float,
) -> dict[str, Any]:
    outp = Path(out_dir)
    outp.mkdir(parents=True, exist_ok=True)

    engineered, team_rows, last_elo_end, last_team_state, goals_report = build_engineered_dataset(
        matches_path=matches_path,
        goals_path=goals_path,
        use_goals_features=use_goals_features,
    )

    # Save engineered dataset artifact
    training_dataset_path = outp / "training_dataset.csv"
    engineered.to_csv(training_dataset_path, index=False)

    feature_cols = _feature_columns(use_goals_features=use_goals_features)
    target_col = "y_upset_avoid_loss"

    engineered = engineered.sort_values(["match_dt", "match_id"]).reset_index(drop=True)
    train_df = engineered[engineered["match_dt"] < VALID_START_DATE].copy()
    val_df = engineered[engineered["match_dt"] >= VALID_START_DATE].copy()

    if len(train_df) < 10:
        raise ValueError(f"Not enough training rows before 2022-01-01. Found {len(train_df)}")
    if len(val_df) < 5:
        raise ValueError(f"Not enough validation rows on/after 2022-01-01. Found {len(val_df)}")

    split_idx = int(round(len(train_df) * 0.8))
    split_idx = max(1, min(split_idx, len(train_df) - 1))
    fit_df = train_df.iloc[:split_idx].copy()
    cal_df = train_df.iloc[split_idx:].copy()

    x_fit_raw = _to_numeric_X(fit_df, feature_cols)
    x_cal_raw = _to_numeric_X(cal_df, feature_cols)
    x_val_raw = _to_numeric_X(val_df, feature_cols)

    x_fit, [x_cal, x_val], fit_medians = _impute_from_fit(x_fit_raw, x_cal_raw, x_val_raw)

    y_fit = pd.to_numeric(fit_df[target_col], errors="coerce").fillna(0).astype(int).to_numpy()
    y_cal = pd.to_numeric(cal_df[target_col], errors="coerce").fillna(0).astype(int).to_numpy()
    y_val = pd.to_numeric(val_df[target_col], errors="coerce").fillna(0).astype(int).to_numpy()

    if len(np.unique(y_fit)) < 2:
        raise ValueError("fit_df contains only one class; cannot train binary classifier.")

    # Hyperparameter search on fit/cal split to improve AUC.
    xgb, chosen_xgb_params, tuning_table = _fit_best_xgb_candidate(
        x_fit=x_fit,
        y_fit=y_fit,
        x_cal=x_cal,
        y_cal=y_cal,
        x_val=x_val,
        y_val=y_val,
    )

    _assert_booster_valid(xgb, x_fit_raw)

    p_raw_val = xgb.predict_proba(x_val)[:, 1]
    raw_metrics = _metrics_dict(y_val, p_raw_val)

    calibrator: CalibratedClassifierCV | None = None
    calibrated_metrics: dict[str, float | None] | None = None
    p_cal_val: np.ndarray | None = None

    if len(cal_df) >= 50 and len(np.unique(y_cal)) >= 2:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            calibrator = CalibratedClassifierCV(xgb, method="sigmoid", cv="prefit")
            calibrator.fit(x_cal, y_cal)
        p_cal_val = calibrator.predict_proba(x_val)[:, 1]
        calibrated_metrics = _metrics_dict(y_val, p_cal_val)

    p_used = p_cal_val if p_cal_val is not None else p_raw_val

    cal_table = _calibration_table(y_val, p_used, bins=10)
    alert_cm = _extract_confusion(y_val, p_used, threshold=alert_threshold)

    p_base = _baseline_elo_probability(val_df["elo_diff"].to_numpy(dtype=float))
    baseline_metrics = _metrics_dict(y_val, p_base)

    booster = xgb.get_booster()
    best_iter = int(getattr(xgb, "best_iteration", -1))
    estimator_cap = int(chosen_xgb_params.get("n_estimators", 0))
    used_ratio = float((best_iter + 1) / estimator_cap) if estimator_cap > 0 and best_iter >= 0 else None
    top_features = _top_feature_gain(booster, feature_cols, top_k=10)

    # Reporting
    print("\n=== Validation Metrics ===")
    print(f"Chosen XGB params: {chosen_xgb_params}")
    print(f"Best iteration: {best_iter} / cap={estimator_cap} (utilization={None if used_ratio is None else round(used_ratio, 3)})")
    if used_ratio is not None and used_ratio < 0.1:
        print("Note: low tree utilization; model likely saturates early on current feature signal.")
    print(f"RAW:       AUC={raw_metrics['auc']} Brier={raw_metrics['brier']} LogLoss={raw_metrics['logloss']}")
    if calibrated_metrics is not None:
        print(f"CALIBRATED: AUC={calibrated_metrics['auc']} Brier={calibrated_metrics['brier']} LogLoss={calibrated_metrics['logloss']}")
    else:
        print("CALIBRATED: skipped (guard triggered)")
    print(f"BASELINE(ELO-only): AUC={baseline_metrics['auc']} Brier={baseline_metrics['brier']} LogLoss={baseline_metrics['logloss']}")
    print(f"Alert@{alert_threshold:.2f}: TP={alert_cm['tp']} FP={alert_cm['fp']} TN={alert_cm['tn']} FN={alert_cm['fn']}")
    print("\nTop feature gain:")
    for item in top_features:
        print(f"  {item['feature']}: {item['gain']:.6f}")

    eval_report = {
        "n_rows_total": int(len(engineered)),
        "n_rows_train": int(len(train_df)),
        "n_rows_fit": int(len(fit_df)),
        "n_rows_cal": int(len(cal_df)),
        "n_rows_valid": int(len(val_df)),
        "world_cup_rows_total": int(engineered["is_world_cup"].sum()) if "is_world_cup" in engineered.columns else None,
        "world_cup_share_total": float(engineered["is_world_cup"].mean()) if "is_world_cup" in engineered.columns else None,
        "feature_columns": feature_cols,
        "target_column": target_col,
        "split": {"train_before": "2022-01-01", "valid_from": "2022-01-01"},
        "goals_features": goals_report,
        "metrics_raw": raw_metrics,
        "metrics_calibrated": calibrated_metrics,
        "metrics_baseline_elo": baseline_metrics,
        "calibration_table_used_probs_10_bins": cal_table,
        "alert_threshold": float(alert_threshold),
        "alert_confusion": alert_cm,
        "top_features_gain": top_features,
        "num_boosted_rounds": int(booster.num_boosted_rounds()),
        "chosen_xgb_params": chosen_xgb_params,
        "xgb_tuning_table": tuning_table,
        "xgb_best_iteration": best_iter,
        "xgb_estimator_cap": estimator_cap,
        "xgb_utilization_ratio": used_ratio,
    }

    # Save model artifacts
    xgb_model_path = outp / "xgb_model.json"
    calibrator_path = outp / "calibrator.pkl"
    feature_list_path = outp / "feature_list.json"
    eval_report_path = outp / "eval_report.json"

    xgb.save_model(str(xgb_model_path))
    joblib.dump(calibrator, calibrator_path)

    feature_info = {
        "feature_columns": feature_cols,
        "fit_medians": {k: float(v) for k, v in fit_medians.to_dict().items()},
        "use_goals_features": bool(use_goals_features),
        "alert_threshold": float(alert_threshold),
        "w_player": float(W_PLAYER),
        "w_team": float(W_TEAM),
        "star_sigma": float(STAR_SIGMA),
        "team_sigma": float(TEAM_SIGMA),
        "z_clip": float(Z_CLIP),
        "delta_logit_cap": float(DELTA_LOGIT_CAP),
        "last_elo_end": {k: float(v) for k, v in last_elo_end.items()},
        "last_team_state": _convert_state_for_json(last_team_state),
        "valid_start_date": "2022-01-01",
    }
    _save_json(feature_list_path, feature_info)
    _save_json(eval_report_path, eval_report)

    # Step 6 + Step 9: demo predictions artifact
    fc_team = load_fc_team_table(top10_fc_path)
    elo_external = load_external_elo(teams_elo_path)
    demo_path = outp / "demo_predictions_top10.csv"
    demo_df = generate_demo_predictions(
        xgb_model=xgb,
        calibrator=calibrator,
        feature_info=feature_info,
        fc_team=fc_team,
        external_elo_map=elo_external,
        out_csv_path=demo_path,
        alert_threshold=alert_threshold,
    )

    print("\nSaved artifacts:")
    print(f"  {xgb_model_path}")
    print(f"  {calibrator_path}")
    print(f"  {feature_list_path}")
    print(f"  {training_dataset_path}")
    print(f"  {eval_report_path}")
    print(f"  {demo_path}")
    print(f"Demo rows: {len(demo_df)}")

    return {
        "xgb_model": xgb,
        "calibrator": calibrator,
        "feature_info": feature_info,
        "fc_team": fc_team,
        "external_elo_map": elo_external,
    }


def load_artifacts_for_inference(out_dir: str | Path) -> tuple[XGBClassifier, CalibratedClassifierCV | None, dict[str, Any]]:
    outp = Path(out_dir)
    xgb_path = outp / "xgb_model.json"
    cal_path = outp / "calibrator.pkl"
    feat_path = outp / "feature_list.json"

    if not xgb_path.exists():
        raise FileNotFoundError(f"Missing artifact: {xgb_path}")
    if not feat_path.exists():
        raise FileNotFoundError(f"Missing artifact: {feat_path}")
    if not cal_path.exists():
        raise FileNotFoundError(f"Missing artifact: {cal_path}")

    model = XGBClassifier()
    model.load_model(str(xgb_path))
    calibrator = joblib.load(cal_path)
    with feat_path.open("r", encoding="utf-8") as fp:
        feature_info = json.load(fp)
    return model, calibrator, feature_info


def generate_demo_predictions(
    xgb_model: XGBClassifier,
    calibrator: CalibratedClassifierCV | None,
    feature_info: dict[str, Any],
    fc_team: pd.DataFrame,
    external_elo_map: dict[str, float],
    out_csv_path: str | Path,
    alert_threshold: float,
) -> pd.DataFrame:
    feature_cols = list(feature_info["feature_columns"])
    fit_medians = pd.Series(feature_info["fit_medians"], dtype=float)
    last_team_state = dict(feature_info.get("last_team_state", {}))
    last_elo_end = {k: float(v) for k, v in feature_info.get("last_elo_end", {}).items()}
    use_goals_features = bool(feature_info.get("use_goals_features", False))

    # Hardcoded 8 matchups among top teams.
    matchups = [
        ("Argentina", "France"),
        ("Brazil", "Spain"),
        ("England", "Portugal"),
        ("Germany", "Netherlands"),
        ("Belgium", "Ivory Coast"),
        ("France", "England"),
        ("Spain", "Germany"),
        ("Portugal", "Argentina"),
    ]

    rows: list[dict[str, Any]] = []
    for home, away in matchups:
        feat_row = build_hypothetical_pre_match_features(
            home_team_name=home,
            away_team_name=away,
            last_team_state=last_team_state,
            last_elo_end=last_elo_end,
            use_goals_features=use_goals_features,
            stage_name="group stage",
        )

        p_model, p_raw = predict_upset_probability(
            feature_row=feat_row,
            xgb_model=xgb_model,
            calibrator=calibrator,
            feature_cols=feature_cols,
            fit_medians=fit_medians,
        )
        payload = dark_score_payload(
            feature_row=feat_row,
            p_model=p_model,
            p_raw=p_raw,
            fc_team=fc_team,
            alert_threshold=alert_threshold,
        )
        ext = compare_external_elo(home, away, external_elo_map)

        row = {
            "home_team": home,
            "away_team": away,
            "home_slug": feat_row["home_slug"],
            "away_slug": feat_row["away_slug"],
            "elo_home_pre_hypo": feat_row["elo_home_pre"],
            "elo_away_pre_hypo": feat_row["elo_away_pre"],
            "favorite_by_elo": payload["favorite_by_elo"],
            "underdog_by_elo": payload["underdog_by_elo"],
            "p_model": payload["p_model"],
            "p_model_raw": payload["p_model_raw"],
            "p_final": payload["p_final"],
            "DarkScore": payload["DarkScore"],
            "Alert": payload["Alert"],
            "fc_used": payload["fc_adjustment"]["used_fc"],
            "fc_delta_logit": payload["fc_adjustment"]["delta_logit"],
            "fc_z_star": payload["fc_adjustment"]["z_star"],
            "fc_z_team": payload["fc_adjustment"]["z_team"],
            "external_elo_home": ext["elo_a"],
            "external_elo_away": ext["elo_b"],
            "external_higher_team": ext["higher_team"],
            "external_p_home_win": ext["p_a_win"],
            "external_p_away_win": ext["p_b_win"],
            "external_pct_point_advantage": ext["pct_point_advantage"],
            "explanation_1": payload["explanations"][0],
            "explanation_2": payload["explanations"][1],
            "explanation_3": payload["explanations"][2],
        }
        rows.append(row)

    demo_df = pd.DataFrame(rows)
    out_path = Path(out_csv_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    demo_df.to_csv(out_path, index=False)
    return demo_df


def print_stack_assessment() -> None:
    print("\n=== Stack Assessment ===")
    print("- Decent for hackathon upset-risk ranking: fast, leak-aware pre-match features, calibrated probabilities, clear alert threshold.")
    print("- What can break: small-sample instability, Elo dominance in sparse contexts, FC overlay sensitivity, and optional goals-event data quality.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Option B (hackathon-optimized) upset model trainer + inference module.")
    parser.add_argument("--train", action="store_true", help="Train model and save artifacts.")
    parser.add_argument("--demo", action="store_true", help="Load artifacts and generate demo_predictions_top10.csv.")
    parser.add_argument("--all", action="store_true", help="Run both train and demo.")

    parser.add_argument("--matches-all-path", default=MATCHES_ALL_PATH)
    parser.add_argument("--goals-all-path", default=GOALS_ALL_PATH)
    parser.add_argument("--top10-fc-path", default=TOP10_FC_PATH)
    parser.add_argument("--teams-elo-path", default=TEAMS_ELO_PATH)
    parser.add_argument("--out-dir", default=OUT_DIR)
    parser.add_argument("--alert-threshold", type=float, default=ALERT_THRESHOLD)
    parser.add_argument(
        "--use-goals-features",
        action=argparse.BooleanOptionalAction,
        default=USE_GOALS_FEATURES,
        help="Enable optional goal-event fragility features (default False).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    do_train = args.train
    do_demo = args.demo
    if args.all or (not do_train and not do_demo):
        do_train = True
        do_demo = True

    model_bundle: dict[str, Any] | None = None

    if do_train:
        model_bundle = train_and_save(
            matches_path=args.matches_all_path,
            goals_path=args.goals_all_path,
            top10_fc_path=args.top10_fc_path,
            teams_elo_path=args.teams_elo_path,
            out_dir=args.out_dir,
            use_goals_features=bool(args.use_goals_features),
            alert_threshold=float(args.alert_threshold),
        )

    if do_demo:
        if model_bundle is None:
            xgb_model, calibrator, feature_info = load_artifacts_for_inference(args.out_dir)
            fc_team = load_fc_team_table(args.top10_fc_path)
            external_elo_map = load_external_elo(args.teams_elo_path)
        else:
            xgb_model = model_bundle["xgb_model"]
            calibrator = model_bundle["calibrator"]
            feature_info = model_bundle["feature_info"]
            fc_team = model_bundle["fc_team"]
            external_elo_map = model_bundle["external_elo_map"]

        demo_path = Path(args.out_dir) / "demo_predictions_top10.csv"
        demo_df = generate_demo_predictions(
            xgb_model=xgb_model,
            calibrator=calibrator,
            feature_info=feature_info,
            fc_team=fc_team,
            external_elo_map=external_elo_map,
            out_csv_path=demo_path,
            alert_threshold=float(args.alert_threshold),
        )
        print(f"\nDemo predictions saved: {demo_path} (rows={len(demo_df)})")

    print_stack_assessment()


if __name__ == "__main__":
    main()
