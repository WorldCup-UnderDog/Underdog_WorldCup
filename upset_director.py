"""
upset_director.py
-----------------
Computes an "Upset Score" for any FIFA World Cup 2026 match result
using the calibrated head-to-head win probabilities from the
logistic regression model (matchup_probs_all_cal).

How the score works:
  - Base upset  : how unlikely was the actual winner? (1 - P(winner))
  - Margin mult : bigger scoreline = more shocking
  - Stage mult  : later rounds amplify the shock
  - Capped at 100
"""

import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# 1.  Load the probability lookup table
# ---------------------------------------------------------------------------

def load_matchup_table(csv_path: str = "nation_matchup_probabilities_proxy_logreg_ALL_pairs_calibrated.csv") -> pd.DataFrame:
    """Load the calibrated matchup probabilities CSV produced by the notebook."""
    df = pd.read_csv(csv_path)
    required = {"team_A", "team_B", "P_team_A_wins", "P_team_B_wins"}
    assert required.issubset(df.columns), f"Missing columns: {required - set(df.columns)}"
    return df


def build_lookup(matchup_df: pd.DataFrame) -> dict:
    """
    Convert the matchup DataFrame into a fast O(1) lookup dict.
    Key  : (team_A_code, team_B_code)
    Value: P(team_A wins)  ∈ (0, 1)
    """
    lookup = {
        (row["team_A"], row["team_B"]): float(row["P_team_A_wins"])
        for _, row in matchup_df.iterrows()
    }
    return lookup


# ---------------------------------------------------------------------------
# 2.  Win probability helper
# ---------------------------------------------------------------------------

def get_win_prob(team_a: str, team_b: str, lookup: dict) -> tuple[float, float]:
    """
    Return (P_a_wins, P_b_wins) for a given matchup.
    Checks both directions in the lookup table.
    """
    if (team_a, team_b) in lookup:
        p_a = lookup[(team_a, team_b)]
    elif (team_b, team_a) in lookup:
        p_a = 1.0 - lookup[(team_b, team_a)]
    else:
        raise ValueError(
            f"No probability found for matchup: {team_a} vs {team_b}. "
            "Check that both nation codes exist in the matchup table."
        )
    return round(p_a, 4), round(1.0 - p_a, 4)


# ---------------------------------------------------------------------------
# 3.  Upset score components
# ---------------------------------------------------------------------------

STAGE_MULTIPLIERS = {
    "Group Stage":    1.00,
    "Round of 32":    1.10,
    "Round of 16":    1.20,
    "Quarter Final":  1.35,
    "Semi Final":     1.50,
    "Final":          2.00,
}


def margin_multiplier(score_winner: int, score_loser: int) -> float:
    """
    Amplifies upset score based on goal difference.
    1-0  → 1.00x  (no amplification)
    2-0  → 1.08x
    3-0  → 1.16x
    4-0  → 1.24x
    ...
    """
    goal_diff = max(score_winner - score_loser, 0)
    return 1.0 + (goal_diff - 1) * 0.08 if goal_diff >= 1 else 1.0


def classify_verdict(score: float, is_upset: bool) -> str:
    if not is_upset:
        if score < 15: return "✅ Dominant Favorite Won"
        if score < 30: return "✅ Expected Result"
        return "⚠️  Favorite Scraped Through"
    else:
        if score < 25: return "🟡 Mild Upset"
        if score < 45: return "🟠 Upset"
        if score < 65: return "🔴 Major Upset"
        if score < 80: return "🚨 Huge Upset"
        return "💥 MASSIVE UPSET"


# ---------------------------------------------------------------------------
# 4.  Main upset_director function
# ---------------------------------------------------------------------------

def upset_director(
    team_a: str,
    team_b: str,
    score_a: int,
    score_b: int,
    lookup: dict,
    stage: str = "Group Stage",
) -> dict:
    """
    Compute the Upset Director score for a completed match.

    Parameters
    ----------
    team_a  : str  — Nation code of Team A (e.g. "ARG", "FRA")
    team_b  : str  — Nation code of Team B
    score_a : int  — Goals scored by Team A
    score_b : int  — Goals scored by Team B
    lookup  : dict — Pre-built probability lookup (from build_lookup())
    stage   : str  — Tournament stage (default "Group Stage")

    Returns
    -------
    dict with upset_score (0–100), verdict, and supporting detail
    """
    if score_a == score_b:
        # Draw: mild shock if the heavier favorite was expected to win
        p_a, p_b = get_win_prob(team_a, team_b, lookup)
        favorite = team_a if p_a >= p_b else team_b
        favorite_win_pct = max(p_a, p_b)
        base = (favorite_win_pct - 0.5) * 100       # 0 for 50/50, up to 50 for sure thing
        upset_score = round(min(base * STAGE_MULTIPLIERS.get(stage, 1.0), 100), 1)
        return {
            "team_a": team_a,
            "team_b": team_b,
            "score": f"{score_a}–{score_b}",
            "result_type": "Draw",
            "favorite": favorite,
            "favorite_win_pct": round(favorite_win_pct * 100, 1),
            "upset_score": upset_score,
            "verdict": f"🤝 Draw (expected favorite: {favorite} at {round(favorite_win_pct*100,1)}%)",
            "stage": stage,
        }

    # Determine actual winner and loser
    if score_a > score_b:
        winner, loser = team_a, team_b
        score_winner, score_loser = score_a, score_b
    else:
        winner, loser = team_b, team_a
        score_winner, score_loser = score_b, score_a

    # Get pre-match win probabilities
    p_a, p_b = get_win_prob(team_a, team_b, lookup)
    p_winner = p_a if winner == team_a else p_b

    # Was the actual winner the pre-match favorite?
    is_upset = p_winner < 0.5

    # Base upset: how unlikely was the winner?
    base = (1.0 - p_winner) * 100

    # Multiply by scoreline and tournament stage
    m_mult = margin_multiplier(score_winner, score_loser)
    s_mult = STAGE_MULTIPLIERS.get(stage, 1.0)

    raw = base * m_mult * s_mult
    upset_score = round(min(raw, 100.0), 1)

    return {
        "team_a": team_a,
        "team_b": team_b,
        "score": f"{score_a}–{score_b}",
        "result_type": "Upset" if is_upset else "Expected",
        "winner": winner,
        "loser": loser,
        "winner_pre_match_prob": round(p_winner * 100, 1),
        "loser_pre_match_prob": round((1.0 - p_winner) * 100, 1),
        "base_upset_score": round(base, 1),
        "margin_multiplier": round(m_mult, 3),
        "stage_multiplier": s_mult,
        "upset_score": upset_score,
        "verdict": classify_verdict(upset_score, is_upset),
        "stage": stage,
    }


# ---------------------------------------------------------------------------
# 5.  Batch scoring utility
# ---------------------------------------------------------------------------

def score_multiple_matches(matches: list[dict], lookup: dict) -> pd.DataFrame:
    """
    Score a list of completed matches.
    Each item in `matches` should be a dict with keys:
      team_a, team_b, score_a, score_b, stage (optional)

    Returns a DataFrame sorted by upset_score descending.
    """
    results = []
    for m in matches:
        try:
            r = upset_director(
                team_a=m["team_a"],
                team_b=m["team_b"],
                score_a=m["score_a"],
                score_b=m["score_b"],
                lookup=lookup,
                stage=m.get("stage", "Group Stage"),
            )
            results.append(r)
        except ValueError as e:
            results.append({"team_a": m["team_a"], "team_b": m["team_b"], "error": str(e)})

    return pd.DataFrame(results).sort_values("upset_score", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# 6.  Quick demo / sanity check
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import os

    csv_file = "nation_matchup_probabilities_proxy_logreg_ALL_pairs_calibrated.csv"

    if not os.path.exists(csv_file):
        print(f"⚠️  '{csv_file}' not found in working directory.")
        print("Run this script from the same folder as the CSV, or adjust csv_path.")
    else:
        df = load_matchup_table(csv_file)
        lookup = build_lookup(df)
        nations_available = sorted(set(df["team_A"]))
        print(f"✅ Loaded {len(df):,} matchup rows.")
        print(f"📋 Available nation codes: {', '.join(nations_available)}\n")

        VALID_STAGES = list(STAGE_MULTIPLIERS.keys())

        while True:
            print("=" * 50)
            print("       ⚽  UPSET DIRECTOR — Match Input")
            print("=" * 50)

            # Team A
            while True:
                team_a = input("Enter Team A nation code (e.g. ARG): ").strip().upper()
                if team_a in lookup or any(team_a == k[0] for k in lookup):
                    break
                print(f"  ❌ '{team_a}' not found. Available: {', '.join(nations_available)}")

            # Team B
            while True:
                team_b = input("Enter Team B nation code (e.g. FRA): ").strip().upper()
                if team_b == team_a:
                    print("  ❌ Team B must be different from Team A.")
                    continue
                if team_b in lookup or any(team_b == k[1] for k in lookup):
                    break
                print(f"  ❌ '{team_b}' not found. Available: {', '.join(nations_available)}")

            # Scores
            while True:
                try:
                    score_a = int(input(f"Score for {team_a}: "))
                    score_b = int(input(f"Score for {team_b}: "))
                    if score_a < 0 or score_b < 0:
                        print("  ❌ Scores must be 0 or greater.")
                        continue
                    break
                except ValueError:
                    print("  ❌ Please enter whole numbers.")

            stage = "Group Stage"

            # Compute and display result
            print()
            try:
                result = upset_director(team_a, team_b, score_a, score_b, lookup, stage)

                print("=" * 50)
                print(f"  {result['verdict']}")
                print(f"  {team_a}  {score_a} – {score_b}  {team_b}  |  {stage}")
                if result["result_type"] == "Draw":
                    print(f"  Expected favorite: {result['favorite']} ({result['favorite_win_pct']}%)")
                else:
                    print(f"  Winner ({result['winner']}) was given a {result['winner_pre_match_prob']}% chance pre-match")
                    print(f"  Margin multiplier: {result['margin_multiplier']}x  |  Stage multiplier: {result['stage_multiplier']}x")
                print(f"  🎯 Upset Score: {result['upset_score']} / 100")
                print("=" * 50)

            except ValueError as e:
                print(f"  ❌ Error: {e}")

            # Ask to continue
            print()
            again = input("Score another match? (y/n): ").strip().lower()
            if again != "y":
                print("\n👋 Thanks for using Upset Director!")
                break
            print()