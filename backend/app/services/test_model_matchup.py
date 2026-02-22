from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

try:
    from app.services.model_predictor import (
        GOALS_ALL_PATH,
        MATCHES_ALL_PATH,
        build_engineered_dataset,
        load_artifacts_for_inference,
        predict_upset_probability,
    )
except ModuleNotFoundError:
    # Support direct script execution from repo root:
    # python3 backend/app/services/test_model_matchup.py ...
    backend_dir = Path(__file__).resolve().parents[2]
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    from app.services.model_predictor import (
        GOALS_ALL_PATH,
        MATCHES_ALL_PATH,
        build_engineered_dataset,
        load_artifacts_for_inference,
        predict_upset_probability,
    )


DEFAULT_ARTIFACT_DIR = Path("artifacts")
DEFAULT_TARGET_COL = "y_upset_avoid_loss"


def _pair_mask(df: pd.DataFrame, country_a: str, country_b: str) -> pd.Series:
    a = country_a.strip().lower()
    b = country_b.strip().lower()
    home = df["home_team_name"].astype(str).str.lower()
    away = df["away_team_name"].astype(str).str.lower()
    return ((home == a) & (away == b)) | ((home == b) & (away == a))


def _infer_underdog_from_row(row: pd.Series) -> tuple[str, str]:
    home_team = str(row.get("home_team_name", "home"))
    away_team = str(row.get("away_team_name", "away"))
    elo_diff = float(row.get("elo_diff", 0.0))

    # Option-B rule: underdog is lower Elo, tie -> away.
    if elo_diff < 0:
        return home_team, "home"
    return away_team, "away"


def _load_feature_info(artifact_dir: Path) -> dict:
    path = artifact_dir / "feature_list.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Missing feature list artifact at {path}. "
            "Train first via: python3 backend/app/services/model_predictor.py --train"
        )
    return json.loads(path.read_text(encoding="utf-8"))


def run_matchup_test(
    country_a: str,
    country_b: str,
    matches_path: Path,
    goals_path: Path,
    artifact_dir: Path,
    threshold: float,
) -> None:
    xgb_model, calibrator, feature_info = load_artifacts_for_inference(artifact_dir)

    use_goals_features = bool(feature_info.get("use_goals_features", False))
    feature_cols = list(feature_info.get("feature_columns", []))
    fit_medians = pd.Series(feature_info.get("fit_medians", {}), dtype=float)

    engineered, _, _, _, _ = build_engineered_dataset(
        matches_path=matches_path,
        goals_path=goals_path,
        use_goals_features=use_goals_features,
    )

    target_col = DEFAULT_TARGET_COL if DEFAULT_TARGET_COL in engineered.columns else "y_upset"
    if target_col not in engineered.columns:
        raise ValueError(f"Target column not found in engineered dataset: {target_col}")

    mask = _pair_mask(engineered, country_a, country_b)
    pair_df = engineered.loc[mask].copy().sort_values(["match_dt", "match_id"]).reset_index(drop=True)

    if pair_df.empty:
        raise ValueError(
            f"No historical rows found for '{country_a}' vs '{country_b}' in {matches_path}."
        )

    probs: list[float] = []
    raw_probs: list[float] = []
    for _, row in pair_df.iterrows():
        p_model, p_raw = predict_upset_probability(
            feature_row=row.to_dict(),
            xgb_model=xgb_model,
            calibrator=calibrator,
            feature_cols=feature_cols,
            fit_medians=fit_medians,
        )
        probs.append(float(p_model))
        raw_probs.append(float(p_raw))

    probs_arr = np.array(probs, dtype=float)
    raw_arr = np.array(raw_probs, dtype=float)
    y_true = pd.to_numeric(pair_df[target_col], errors="coerce").fillna(0).astype(int).to_numpy()
    preds = (probs_arr >= threshold).astype(int)

    n_rows = len(pair_df)
    accuracy = float((preds == y_true).mean())
    mean_likelihood = float(np.mean(probs_arr))

    latest_prob = float(probs_arr[-1])
    latest_raw = float(raw_arr[-1])
    latest_pred = int(preds[-1])
    latest_true = int(y_true[-1])
    latest_match = pair_df.iloc[-1]
    latest_underdog_team, latest_underdog_side = _infer_underdog_from_row(latest_match)

    print(f"Matchup Test: {country_a} vs {country_b}")
    print(
        "Target definition: y_upset_avoid_loss=1 means the underdog "
        "(lower pre-match Elo, tie->away) avoided loss (win/draw)."
    )
    print(f"Rows evaluated: {n_rows}")
    if n_rows <= 3:
        print(
            f"Note: Accuracy can look extreme on tiny samples. Here n={n_rows}, "
            "so accuracy=1.0 can happen with one correct row."
        )
    print(f"Accuracy (@ threshold={threshold:.2f}): {accuracy:.4f}")
    print(f"Likelihood (avg upset avoid-loss probability): {mean_likelihood:.4f}")
    print("")
    print("Latest historical matchup prediction:")
    print(f"  Date: {latest_match.get('match_date', latest_match.get('match_dt', 'N/A'))}")
    print(f"  Home: {latest_match['home_team_name']}")
    print(f"  Away: {latest_match['away_team_name']}")
    print(f"  Underdog by Elo: {latest_underdog_team} ({latest_underdog_side})")
    print("  Prediction mode: full Option-B model")
    print(f"  Prediction (upset avoid loss): {latest_pred} (prob={latest_prob:.4f})")
    print(f"  Actual: {latest_true}")
    print("")
    print("Per-match probabilities:")

    out = pair_df[["match_id", "match_date", "home_team_name", "away_team_name", target_col]].copy()
    out["raw_model_prob"] = raw_arr
    out["pred_prob_upset_avoid_loss"] = probs_arr
    out["pred_label"] = preds
    print(out.to_string(index=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Test Option-B upset model predictions between two countries.")
    parser.add_argument("--country-a", required=True, help="First country/team name.")
    parser.add_argument("--country-b", required=True, help="Second country/team name.")
    parser.add_argument(
        "--matches-path",
        type=Path,
        default=Path(MATCHES_ALL_PATH),
        help=f"Matches CSV path (default: {MATCHES_ALL_PATH})",
    )
    parser.add_argument(
        "--goals-path",
        type=Path,
        default=Path(GOALS_ALL_PATH),
        help=f"Goals CSV path (default: {GOALS_ALL_PATH})",
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=DEFAULT_ARTIFACT_DIR,
        help="Artifact directory containing xgb_model.json, calibrator.pkl, feature_list.json",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.60,
        help="Classification threshold for upset alert label.",
    )
    args = parser.parse_args()

    run_matchup_test(
        country_a=args.country_a,
        country_b=args.country_b,
        matches_path=args.matches_path,
        goals_path=args.goals_path,
        artifact_dir=args.artifact_dir,
        threshold=args.threshold,
    )


if __name__ == "__main__":
    main()
