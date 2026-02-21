# Locate and load a file named like 'combined_players_stats' into a DataFrame
import os
import glob
import pandas as pd

combined_players_stats = pd.read_csv("/Users/arjunramakrishnan/Downloads/Match-Prediction-Model-main/combined_players_stats.csv")

print(combined_players_stats)

# Drop the 'Team' and 'League' columns from combined_players_stats
cols_to_drop = [c for c in ["Team", "League"] if c in combined_players_stats.columns]
combined_players_stats = combined_players_stats.drop(columns=cols_to_drop)

print("Dropped columns:", cols_to_drop)
print("New shape:", combined_players_stats.shape)
print("Remaining columns (first 15):", list(combined_players_stats.columns[:15]))

# Inspect and normalize the Nation field so we can filter by allowed countries
# FBref-style Nation often looks like 'eng ENG' (lowercase tag + uppercase FIFA trigram)

nation_raw = combined_players_stats['Nation'].astype(str)
combined_players_stats['Nation_code'] = nation_raw.str.extract(r'([A-Z]{3})', expand=False)
combined_players_stats['Nation_tag'] = nation_raw.str.extract(r'^([a-z]{2,3})', expand=False)

print('Nation raw sample:')

print('Unique Nation_code count:', combined_players_stats['Nation_code'].nunique(dropna=True))
print('Top 20 Nation_code values:')
print(combined_players_stats['Nation_code'].value_counts(dropna=False).head(20))


# Filter players to an allowed list of countries (by Nation_code), and report counts

allowed_country_names = [
    "Algeria","Argentina","Australia","Austria","Belgium","Brazil","Canada","Cape Verde","Colombia",
    "Croatia","Curacao","Ecuador","Egypt","England","France","Germany","Ghana","Haiti","IR Iran",
    "Ivory Coast","Japan","Jordan","Mexico","Morocco","Netherlands","New Zealand","Norway","Panama",
    "Paraguay","Portugal","Qatar","Saudi Arabia","Scotland","Senegal","South Africa","South Korea",
    "Spain","Switzerland","Tunisia","United States","Uruguay","Uzbekistan"
]

# Common FIFA/FBref 3-letter codes for the listed countries
name_to_code = {
    "Algeria": "ALG",
    "Argentina": "ARG",
    "Australia": "AUS",
    "Austria": "AUT",
    "Belgium": "BEL",
    "Brazil": "BRA",
    "Canada": "CAN",
    "Cape Verde": "CPV",
    "Colombia": "COL",
    "Croatia": "CRO",
    "Curacao": "CUW",
    "Ecuador": "ECU",
    "Egypt": "EGY",
    "England": "ENG",
    "France": "FRA",
    "Germany": "GER",
    "Ghana": "GHA",
    "Haiti": "HAI",
    "IR Iran": "IRN",
    "Ivory Coast": "CIV",
    "Japan": "JPN",
    "Jordan": "JOR",
    "Mexico": "MEX",
    "Morocco": "MAR",
    "Netherlands": "NED",
    "New Zealand": "NZL",
    "Norway": "NOR",
    "Panama": "PAN",
    "Paraguay": "PAR",
    "Portugal": "POR",
    "Qatar": "QAT",
    "Saudi Arabia": "KSA",
    "Scotland": "SCO",
    "Senegal": "SEN",
    "South Africa": "RSA",
    "South Korea": "KOR",
    "Spain": "ESP",
    "Switzerland": "SUI",
    "Tunisia": "TUN",
    "United States": "USA",
    "Uruguay": "URU",
    "Uzbekistan": "UZB",
}

allowed_codes = sorted({name_to_code.get(n) for n in allowed_country_names if name_to_code.get(n) is not None})
missing = sorted([n for n in allowed_country_names if n not in name_to_code])

before_n = len(combined_players_stats)
filtered_players_stats = combined_players_stats[combined_players_stats["Nation_code"].isin(allowed_codes)].copy()
after_n = len(filtered_players_stats)

print(f"Allowed countries: {len(allowed_country_names)}")
print(f"Allowed codes mapped: {len(allowed_codes)}")
print("Missing name->code mappings:", missing if missing else "<none>")
print(f"Rows before: {before_n:,} | after: {after_n:,} | removed: {before_n - after_n:,}")

print("\nNation_code distribution (kept; top 20):")
print(filtered_players_stats["Nation_code"].value_counts().head(20))


filtered_players_stats.columns

# Create a coarse position group (GK/DEF/MID/FWD) from the FBref 'Pos' column

def pos_to_group(pos_val: str) -> str:
    if pd.isna(pos_val):
        return pd.NA
    s = str(pos_val).upper()
    # FBref often uses: GK, DF, MF, FW and combos like 'MF,FW'
    parts = [p.strip() for p in s.replace(';', ',').split(',') if p.strip()]

    if 'GK' in parts:
        return 'GK'
    # If multiple positions, prefer more attacking role for simplicity
    if 'FW' in parts:
        return 'FWD'
    if 'MF' in parts:
        return 'MID'
    if 'DF' in parts:
        return 'DEF'
    return pd.NA

filtered_players_stats['Pos_group'] = filtered_players_stats['Pos'].apply(pos_to_group)

print('Pos_group value counts:')
print(filtered_players_stats['Pos_group'].value_counts(dropna=False))

print('\nSample rows by Pos_group:')


# Define position-based weights for selected per-90 and progression features (no scoring yet)
import numpy as np

# Feature columns to be used (existing in filtered_players_stats)
feature_cols = {
    "gls_p90": "Per 90 Minutes Gls",
    "ast_p90": "Per 90 Minutes Ast",
    "xg_p90": "Per 90 Minutes xG",
    "xag_p90": "Per 90 Minutes xAG",
    "prgc": "Progression PrgC",
    "prgp": "Progression PrgP",
    "prgr": "Progression PrgR",
    "crdy": "Performance CrdY",
    "crdr": "Performance CrdR",
}

# Stars → numeric weights (simple linear: 1★=1, 2★=2, 3★=3)
# Cards are handled separately as penalties (subtracted), so weights here are positive magnitudes.
weights_by_pos = {
    "GK": {  # not specified by user; set to 0 for these attacking/progression features by default
        "gls_p90": 0, "ast_p90": 0, "xg_p90": 0, "xag_p90": 0,
        "prgc": 0, "prgp": 0, "prgr": 0,
        "crdy": 1, "crdr": 1,
    },
    "DEF": {
        "gls_p90": 1,
        "ast_p90": 2,
        "xg_p90": 1,
        "xag_p90": 2,
        "prgc": 3,
        "prgp": 3,
        "prgr": 3,
        "crdy": 1,
        "crdr": 1,
    },
    "MID": {
        "gls_p90": 2,
        "ast_p90": 3,
        "xg_p90": 2,
        "xag_p90": 3,
        "prgc": 3,
        "prgp": 3,
        "prgr": 3,
        "crdy": 1,
        "crdr": 1,
    },
    "FWD": {
        "gls_p90": 3,
        "ast_p90": 2,
        "xg_p90": 3,
        "xag_p90": 2,
        "prgc": 2,
        "prgp": 2,
        "prgr": 2,
        "crdy": 1,
        "crdr": 1,
    },
}

# Quick column existence check
missing_cols = [col for col in feature_cols.values() if col not in filtered_players_stats.columns]
print("Missing required columns:", missing_cols if missing_cols else "<none>")

print("Available Pos_group values:", sorted(filtered_players_stats["Pos_group"].dropna().unique().tolist()))
print("Weights keys:", list(weights_by_pos.keys()))


# Compute a position-specific weighted score using the defined weights
# - Uses per-90 attacking metrics + progression metrics
# - Subtracts card contributions (CrdY/CrdR)
# - Uses (xG_p90 + npxG_p90) / 2 to represent "xG / npxG" as a single blended signal

import numpy as np

scoring_df = filtered_players_stats.copy()

# Ensure numeric dtype for scoring columns
num_cols = [
    feature_cols["gls_p90"], feature_cols["ast_p90"], feature_cols["xg_p90"], feature_cols["xag_p90"],
    feature_cols["prgc"], feature_cols["prgp"], feature_cols["prgr"],
    feature_cols["crdy"], feature_cols["crdr"],
    "Per 90 Minutes npxG",
]
for c in num_cols:
    scoring_df[c] = pd.to_numeric(scoring_df[c], errors="coerce")

# Blended xG/npxG per 90 (user requested xG / npxG)
scoring_df["xg_npxg_p90_blend"] = scoring_df[[feature_cols["xg_p90"], "Per 90 Minutes npxG"]].mean(axis=1)

# Helper to compute row-wise weighted score based on Pos_group
keys_positive = ["gls_p90", "ast_p90", "xg_p90", "xag_p90", "prgc", "prgp", "prgr"]

def compute_weighted_score(row):
    pos = row.get("Pos_group")
    if pd.isna(pos) or pos not in weights_by_pos:
        return np.nan

    w = weights_by_pos[pos]

    # Positive contributions
    gls = row[feature_cols["gls_p90"]]
    ast = row[feature_cols["ast_p90"]]
    xg_blend = row["xg_npxg_p90_blend"]
    xag = row[feature_cols["xag_p90"]]
    prgc = row[feature_cols["prgc"]]
    prgp = row[feature_cols["prgp"]]
    prgr = row[feature_cols["prgr"]]

    # Use the xG weight for the blended xG/npxG signal
    pos_score = (
        w["gls_p90"] * gls +
        w["ast_p90"] * ast +
        w["xg_p90"] * xg_blend +
        w["xag_p90"] * xag +
        w["prgc"] * prgc +
        w["prgp"] * prgp +
        w["prgr"] * prgr
    )

    # Card penalties (subtract)
    crdy = row[feature_cols["crdy"]]
    crdr = row[feature_cols["crdr"]]
    pos_score = pos_score - (w["crdy"] * crdy + w["crdr"] * crdr)

    return pos_score

scoring_df["weighted_score"] = scoring_df.apply(compute_weighted_score, axis=1)

print("Weighted score computed.")
print("Missing weighted_score:", scoring_df["weighted_score"].isna().mean())


print("\nTop 10 by position group:")
for g in ["FWD","MID","DEF","GK"]:
    sub = scoring_df[scoring_df["Pos_group"]==g].sort_values("weighted_score", ascending=False)
    print(f"\n{g} (n={len(sub)}):")


# Create a normalized, position-weighted score that avoids domination by raw progression totals
# - Convert PrgC/PrgP/PrgR totals to per-90 equivalents using Playing Time 90s
# - Recompute weighted_score_norm using the same star weights
# - Provide basic summaries and top players per position (with a minutes filter)

import numpy as np

scoring_norm_df = filtered_players_stats.copy()

# Ensure numeric columns
cols_needed = [
    feature_cols["gls_p90"], feature_cols["ast_p90"], feature_cols["xg_p90"], feature_cols["xag_p90"],
    feature_cols["prgc"], feature_cols["prgp"], feature_cols["prgr"],
    feature_cols["crdy"], feature_cols["crdr"],
    "Per 90 Minutes npxG",
    "Playing Time 90s",
]
for c in cols_needed:
    scoring_norm_df[c] = pd.to_numeric(scoring_norm_df[c], errors="coerce")

# Per-90 progression (handle divide-by-zero safely)
minutes_90s = scoring_norm_df["Playing Time 90s"].replace({0: np.nan})
scoring_norm_df["PrgC_p90"] = scoring_norm_df[feature_cols["prgc"]] / minutes_90s
scoring_norm_df["PrgP_p90"] = scoring_norm_df[feature_cols["prgp"]] / minutes_90s
scoring_norm_df["PrgR_p90"] = scoring_norm_df[feature_cols["prgr"]] / minutes_90s

# Blend xG/npxG per 90
scoring_norm_df["xg_npxg_p90_blend"] = scoring_norm_df[[feature_cols["xg_p90"], "Per 90 Minutes npxG"]].mean(axis=1)

def compute_weighted_score_norm(row):
    pos = row.get("Pos_group")
    if pd.isna(pos) or pos not in weights_by_pos:
        return np.nan
    w = weights_by_pos[pos]

    # positive
    pos_score = (
        w["gls_p90"] * row[feature_cols["gls_p90"]] +
        w["ast_p90"] * row[feature_cols["ast_p90"]] +
        w["xg_p90"] * row["xg_npxg_p90_blend"] +
        w["xag_p90"] * row[feature_cols["xag_p90"]] +
        w["prgc"] * row["PrgC_p90"] +
        w["prgp"] * row["PrgP_p90"] +
        w["prgr"] * row["PrgR_p90"]
    )

    # subtract cards
    pos_score = pos_score - (w["crdy"] * row[feature_cols["crdy"]] + w["crdr"] * row[feature_cols["crdr"]])
    return pos_score

scoring_norm_df["weighted_score_norm"] = scoring_norm_df.apply(compute_weighted_score_norm, axis=1)

# Quick summaries
print("weighted_score_norm missing rate:", scoring_norm_df["weighted_score_norm"].isna().mean())
print("weighted_score_norm summary (all players):")

# Minutes filter for more stable rankings
min_90s = 10
eligible = scoring_norm_df[scoring_norm_df["Playing Time 90s"] >= min_90s].copy()
print(f"\nEligible players with Playing Time 90s >= {min_90s}: {len(eligible):,} / {len(scoring_norm_df):,}")

print("\nTop 10 overall (eligible):")

for g in ["FWD","MID","DEF","GK"]:
    subg = eligible[eligible["Pos_group"]==g].sort_values("weighted_score_norm", ascending=False)
    print(f"\nTop 10 {g} (eligible; n={len(subg)}):")

# Create an improved normalized score: progression per-90 AND cards per-90 (instead of season totals)
import numpy as np

scoring_norm2_df = filtered_players_stats.copy()

# Ensure numeric columns used
cols_needed2 = [
    feature_cols["gls_p90"], feature_cols["ast_p90"], feature_cols["xg_p90"], feature_cols["xag_p90"],
    feature_cols["prgc"], feature_cols["prgp"], feature_cols["prgr"],
    feature_cols["crdy"], feature_cols["crdr"],
    "Per 90 Minutes npxG", "Playing Time 90s",
]
for c in cols_needed2:
    scoring_norm2_df[c] = pd.to_numeric(scoring_norm2_df[c], errors="coerce")

# Avoid divide-by-zero
n90 = scoring_norm2_df["Playing Time 90s"].replace({0: np.nan})

# Per-90 rate conversions for totals
scoring_norm2_df["PrgC_p90"] = scoring_norm2_df[feature_cols["prgc"]] / n90
scoring_norm2_df["PrgP_p90"] = scoring_norm2_df[feature_cols["prgp"]] / n90
scoring_norm2_df["PrgR_p90"] = scoring_norm2_df[feature_cols["prgr"]] / n90
scoring_norm2_df["CrdY_p90"] = scoring_norm2_df[feature_cols["crdy"]] / n90
scoring_norm2_df["CrdR_p90"] = scoring_norm2_df[feature_cols["crdr"]] / n90

# xG/npxG blend per 90
scoring_norm2_df["xg_npxg_p90_blend"] = scoring_norm2_df[[feature_cols["xg_p90"], "Per 90 Minutes npxG"]].mean(axis=1)


def compute_weighted_score_norm2(row):
    pos = row.get("Pos_group")
    if pd.isna(pos) or pos not in weights_by_pos:
        return np.nan
    w = weights_by_pos[pos]

    # positive contributions
    score = (
        w["gls_p90"] * row[feature_cols["gls_p90"]] +
        w["ast_p90"] * row[feature_cols["ast_p90"]] +
        w["xg_p90"] * row["xg_npxg_p90_blend"] +
        w["xag_p90"] * row[feature_cols["xag_p90"]] +
        w["prgc"] * row["PrgC_p90"] +
        w["prgp"] * row["PrgP_p90"] +
        w["prgr"] * row["PrgR_p90"]
    )

    # subtract card rates (per 90)
    score = score - (w["crdy"] * row["CrdY_p90"] + w["crdr"] * row["CrdR_p90"])
    return score

scoring_norm2_df["weighted_score_norm2"] = scoring_norm2_df.apply(compute_weighted_score_norm2, axis=1)

print("weighted_score_norm2 missing rate:", scoring_norm2_df["weighted_score_norm2"].isna().mean())

# Create an eligibility cut to stabilize per-90 rates
min_90s_norm2 = 10
eligible2 = scoring_norm2_df[scoring_norm2_df["Playing Time 90s"] >= min_90s_norm2].copy()

print(f"\nEligible2 players with Playing Time 90s >= {min_90s_norm2}: {len(eligible2):,} / {len(scoring_norm2_df):,}")
print("\nTop 10 overall (eligible2):")

for g in ["FWD","MID","DEF"]:
    subg2 = eligible2[eligible2["Pos_group"] == g].sort_values("weighted_score_norm2", ascending=False)
    print(f"\nTop 10 {g} (eligible2; n={len(subg2)}):")

# GK is intentionally near-zero under these attacking/progression features
print("\nGK note: under the requested feature set, GK scores will be ~0 (no GK-relevant features included).")


# Create a final, tidy ranking table from the normalized per-90 score (weighted_score_norm2)
# - Uses eligible2 (Playing Time 90s >= 10)
# - Provides overall and per-position top lists

final_rankings = eligible2.copy()

# Columns to keep for downstream use
keep_cols = [
    "Player","Nation","Nation_code","Pos","Pos_group","Age","Playing Time 90s",
    "weighted_score_norm2",
    feature_cols["gls_p90"], feature_cols["ast_p90"], feature_cols["xg_p90"], "Per 90 Minutes npxG",
    feature_cols["xag_p90"],
    "PrgC_p90","PrgP_p90","PrgR_p90","CrdY_p90","CrdR_p90",
]
keep_cols = [c for c in keep_cols if c in final_rankings.columns]
final_rankings = final_rankings[keep_cols].sort_values("weighted_score_norm2", ascending=False)

print("final_rankings shape:", final_rankings.shape)
print("Score column: weighted_score_norm2 (higher is better)")

print("\nTop 15 overall:")

for g in ["FWD","MID","DEF","GK"]:
    sub = final_rankings[final_rankings["Pos_group"] == g]
    print(f"\nTop 15 {g} (n={len(sub)}):")

# Optional: save to CSV for user download/use
out_path = "final_rankings_weighted_score_norm2.csv"
final_rankings.to_csv(out_path, index=False)
print(f"\nSaved: {out_path}")


# Validate score drivers and create a robust (winsorized + standardized) alternative score by position
import numpy as np
import pandas as pd

# Work from eligible2 (already has per-90 rates + weighted_score_norm2)
robust_df = eligible2.copy()

# Columns that feed the score (per-90 versions)
robust_components = {
    "gls_p90": feature_cols["gls_p90"],
    "ast_p90": feature_cols["ast_p90"],
    "xg_p90": feature_cols["xg_p90"],
    "npxg_p90": "Per 90 Minutes npxG",
    "xag_p90": feature_cols["xag_p90"],
    "prgc_p90": "PrgC_p90",
    "prgp_p90": "PrgP_p90",
    "prgr_p90": "PrgR_p90",
    "crdy_p90": "CrdY_p90",
    "crdr_p90": "CrdR_p90",
}

# Ensure numeric
to_num = list(robust_components.values()) + ["Playing Time 90s", "weighted_score_norm2"]
for c in to_num:
    if c in robust_df.columns:
        robust_df[c] = pd.to_numeric(robust_df[c], errors="coerce")

# xG/npxG blend per-90 (same as earlier)
robust_df["xg_npxg_p90_blend"] = robust_df[[robust_components["xg_p90"], robust_components["npxg_p90"]]].mean(axis=1)

# Quick distribution check (helps spot outliers)
check_cols = [
    "weighted_score_norm2",
    robust_components["prgc_p90"], robust_components["prgp_p90"], robust_components["prgr_p90"],
    robust_components["crdy_p90"], robust_components["crdr_p90"],
]
print("Distribution snapshot (eligible2):")

# Build a robust score: winsorize each component within position group, then z-score within group
# (keeps interpretability: score is still a weighted sum, but components are on comparable scales)

def winsorize_series(s, lo=0.01, hi=0.99):
    qlo, qhi = s.quantile([lo, hi])
    return s.clip(lower=qlo, upper=qhi)

def zscore(s):
    mu = s.mean()
    sd = s.std(ddof=0)
    if sd == 0 or np.isnan(sd):
        return s * 0
    return (s - mu) / sd

robust_score_parts = []

for pos in ["FWD", "MID", "DEF", "GK"]:
    mask = robust_df["Pos_group"] == pos
    if mask.sum() == 0:
        continue

    tmp = robust_df.loc[mask, :].copy()

    # winsorize + zscore components
    for k, col in robust_components.items():
        if col not in tmp.columns:
            continue
        tmp[col + "_w"] = winsorize_series(tmp[col])
        tmp[col + "_z"] = zscore(tmp[col + "_w"])

    tmp["xg_npxg_p90_blend_w"] = winsorize_series(tmp["xg_npxg_p90_blend"])
    tmp["xg_npxg_p90_blend_z"] = zscore(tmp["xg_npxg_p90_blend_w"])

    w = weights_by_pos[pos]

    # Weighted sum on standardized components; cards subtract
    tmp["weighted_score_robust_z"] = (
        w["gls_p90"] * tmp[robust_components["gls_p90"] + "_z"] +
        w["ast_p90"] * tmp[robust_components["ast_p90"] + "_z"] +
        w["xg_p90"]  * tmp["xg_npxg_p90_blend_z"] +
        w["xag_p90"] * tmp[robust_components["xag_p90"] + "_z"] +
        w["prgc"]    * tmp[robust_components["prgc_p90"] + "_z"] +
        w["prgp"]    * tmp[robust_components["prgp_p90"] + "_z"] +
        w["prgr"]    * tmp[robust_components["prgr_p90"] + "_z"] -
        w["crdy"]    * tmp[robust_components["crdy_p90"] + "_z"] -
        w["crdr"]    * tmp[robust_components["crdr_p90"] + "_z"]
    )

    robust_score_parts.append(tmp[["Player","Nation_code","Age","Pos","Pos_group","Playing Time 90s","weighted_score_norm2","weighted_score_robust_z"]])

robust_rankings = pd.concat(robust_score_parts, axis=0).sort_values("weighted_score_robust_z", ascending=False)

print("\nTop 15 overall by robust z-score:")

for pos in ["FWD","MID","DEF","GK"]:
    subpos = robust_rankings[robust_rankings["Pos_group"] == pos].sort_values("weighted_score_robust_z", ascending=False)
    print(f"\nTop 10 {pos} by robust z-score (n={len(subpos)}):")

# Save for comparison
robust_rankings.to_csv("final_rankings_weighted_score_robust_z.csv", index=False)
print("\nSaved: final_rankings_weighted_score_robust_z.csv")


# Create nation-level rankings from player-level final_rankings
import pandas as pd
import numpy as np

# Choose which player-level score to rank nations by
# - 'weighted_score_norm2' is the main per-90 normalized score
# - 'weighted_score_robust_z' is the outlier-resistant alternative (position-standardized)
score_col = "weighted_score_norm2"
alt_score_col = "weighted_score_robust_z" if "weighted_score_robust_z" in robust_rankings.columns else None

# Base table: use final_rankings (already filtered to Playing Time 90s >= 10 and allowed nations)
base = final_rankings.copy()

# Nation summary stats
nation_rankings = (
    base.groupby("Nation_code", as_index=False)
        .agg(
            n_players=("Player", "count"),
            minutes90_sum=("Playing Time 90s", "sum"),
            score_mean=(score_col, "mean"),
            score_median=(score_col, "median"),
            score_top1=(score_col, "max"),
        )
)

# Add a minutes-weighted average score (weights = Playing Time 90s)
def wavg(g, value_col, weight_col):
    v = g[value_col].to_numpy()
    w = g[weight_col].to_numpy()
    m = np.isfinite(v) & np.isfinite(w)
    v = v[m]; w = w[m]
    if w.sum() == 0:
        return np.nan
    return np.sum(v * w) / np.sum(w)

wavg_scores = (
    base.groupby("Nation_code")
        .apply(lambda g: wavg(g, score_col, "Playing Time 90s"), include_groups=False)
        .rename("score_wavg_by_minutes")
        .reset_index()
)

nation_rankings = nation_rankings.merge(wavg_scores, on="Nation_code", how="left")

# Attach best player name per nation for interpretability
idx_best = base.groupby("Nation_code")[score_col].idxmax()
best_players = (
    base.loc[idx_best, ["Nation_code", "Player", "Pos_group", "Playing Time 90s", score_col]]
        .rename(columns={
            "Player": "best_player",
            "Pos_group": "best_player_pos_group",
            "Playing Time 90s": "best_player_90s",
            score_col: "best_player_score",
        })
)

nation_rankings = nation_rankings.merge(best_players, on="Nation_code", how="left")

# Optional: also compute nation aggregates for the robust z-score
if alt_score_col is not None:
    rb = robust_rankings[["Nation_code", "Player", "Playing Time 90s", alt_score_col]].copy()
    rb = rb.merge(base[["Nation_code","Player","Playing Time 90s"]], on=["Nation_code","Player","Playing Time 90s"], how="inner")
    rb_summary = (
        rb.groupby("Nation_code", as_index=False)
          .agg(robust_z_mean=(alt_score_col, "mean"), robust_z_median=(alt_score_col, "median"))
    )
    nation_rankings = nation_rankings.merge(rb_summary, on="Nation_code", how="left")

# Sort nations by minutes-weighted average score as the default nation ranking
nation_rankings = nation_rankings.sort_values(["score_wavg_by_minutes", "score_mean"], ascending=False)

print("Nation rankings table shape:", nation_rankings.shape)
print("Ranking metric (primary): score_wavg_by_minutes using", score_col)


# Save
nation_out_path = "nation_rankings_from_weighted_score_norm2.csv"
nation_rankings.to_csv(nation_out_path, index=False)
print("Saved:", nation_out_path)


# Sort nation_rankings from best-player score to worst-player score

nation_rankings_best_player_sorted = nation_rankings.sort_values(
    ["best_player_score", "score_wavg_by_minutes", "score_mean"],
    ascending=[False, False, False],
).reset_index(drop=True)

print("Nation rankings sorted by best_player_score (desc).")

# Save
out_path_best_player = "nation_rankings_sorted_by_best_player_score.csv"
nation_rankings_best_player_sorted.to_csv(out_path_best_player, index=False)
print("Saved:", out_path_best_player)


# Compute nation "Starting XI Strength" using top 11 players by weighted_score_norm2
import numpy as np
import pandas as pd

score_col = "weighted_score_norm2"
assert score_col in final_rankings.columns, f"Missing {score_col} in final_rankings"

base_xi = final_rankings.copy()

# Rank players within nation by score (descending)
base_xi["rank_in_nation"] = (
    base_xi.groupby("Nation_code")[score_col]
           .rank(method="first", ascending=False)
)

# Keep top 11 (or fewer if nation has <11 eligible players)
xi = base_xi[base_xi["rank_in_nation"] <= 11].copy()

# Aggregate XI strength metrics
nation_xi = (
    xi.groupby("Nation_code", as_index=False)
      .agg(
          n_xi_players=("Player", "count"),
          xi_score_sum=(score_col, "sum"),
          xi_score_mean=(score_col, "mean"),
          xi_score_median=(score_col, "median"),
          xi_score_min=(score_col, "min"),
          xi_score_max=(score_col, "max"),
          xi_minutes90_sum=("Playing Time 90s", "sum"),
      )
)

# Attach the XI list for interpretability
xi_lists = (
    xi.sort_values(["Nation_code", score_col], ascending=[True, False])
      .groupby("Nation_code")
      .apply(lambda g: ", ".join(g["Player"].head(11).tolist()), include_groups=False)
      .rename("starting_xi_players")
      .reset_index()
)

nation_xi = nation_xi.merge(xi_lists, on="Nation_code", how="left")

# Sort nations by XI strength (use mean by default; sum is highly correlated but depends on n_xi_players)
nation_xi = nation_xi.sort_values(["xi_score_mean", "xi_score_sum"], ascending=False).reset_index(drop=True)

print("Nation Starting XI Strength computed from top 11 players by", score_col)
print("Nations:", nation_xi.shape[0])


# Save
out_path_xi = "nation_rankings_starting_xi_top11.csv"
nation_xi.to_csv(out_path_xi, index=False)
print("Saved:", out_path_xi)


# Compute nation "Star Player Impact" = average score of top 3 players by weighted_score_norm2
import pandas as pd

score_col = "weighted_score_norm2"
assert score_col in final_rankings.columns, f"Missing {score_col} in final_rankings"

base_star = final_rankings[["Nation_code", "Player", "Pos_group", "Playing Time 90s", score_col]].copy()

# Sort players within each nation by score (desc), take top 3
star3 = (
    base_star.sort_values(["Nation_code", score_col], ascending=[True, False])
             .groupby("Nation_code")
             .head(3)
             .copy()
)

# Aggregate star player impact
nation_star_impact = (
    star3.groupby("Nation_code", as_index=False)
         .agg(
             n_star_players=("Player", "count"),
             star3_avg_score=(score_col, "mean"),
             star3_sum_score=(score_col, "sum"),
             star3_min_score=(score_col, "min"),
             star3_max_score=(score_col, "max"),
             star3_minutes90_sum=("Playing Time 90s", "sum"),
         )
)

# Add a readable list of the 3 players (with scores)
star3_list = (
    star3.assign(player_with_score=lambda d: d["Player"] + " (" + d[score_col].round(2).astype(str) + ")")
         .groupby("Nation_code")["player_with_score"]
         .apply(lambda s: ", ".join(s.tolist()))
         .rename("star3_players")
         .reset_index()
)

nation_star_impact = nation_star_impact.merge(star3_list, on="Nation_code", how="left")

# Sort by star player impact (avg of top 3)
nation_star_impact = nation_star_impact.sort_values(
    ["star3_avg_score", "star3_max_score"], ascending=False
).reset_index(drop=True)

print("Nation Star Player Impact computed as mean(top 3 players by", score_col + ")")
print("Nations:", nation_star_impact.shape[0])

# Save
out_path_star = "nation_rankings_star_player_impact_top3_avg.csv"
nation_star_impact.to_csv(out_path_star, index=False)
print("Saved:", out_path_star)


# Compute nation "Squad Depth" = average score of players ranked 12–23 by weighted_score_norm2
import pandas as pd

score_col = "weighted_score_norm2"
assert score_col in final_rankings.columns, f"Missing {score_col} in final_rankings"

base_depth = final_rankings[["Nation_code", "Player", "Pos_group", "Playing Time 90s", score_col]].copy()

# Rank players within each nation by score (desc)
base_depth["rank_in_nation"] = (
    base_depth.groupby("Nation_code")[score_col]
              .rank(method="first", ascending=False)
)

# Keep ranks 12–23 inclusive
bench_12_23 = base_depth[(base_depth["rank_in_nation"] >= 12) & (base_depth["rank_in_nation"] <= 23)].copy()

nation_depth = (
    bench_12_23.groupby("Nation_code", as_index=False)
               .agg(
                   n_depth_players=("Player", "count"),
                   depth12_23_avg_score=(score_col, "mean"),
                   depth12_23_sum_score=(score_col, "sum"),
                   depth12_23_min_score=(score_col, "min"),
                   depth12_23_max_score=(score_col, "max"),
                   depth12_23_minutes90_sum=("Playing Time 90s", "sum"),
               )
)

# Add a readable list (up to 12 players) with scores
bench_list = (
    bench_12_23.sort_values(["Nation_code", "rank_in_nation"], ascending=[True, True])
               .assign(player_with_score=lambda d: d["Player"] + " (" + d[score_col].round(2).astype(str) + ")")
               .groupby("Nation_code")["player_with_score"]
               .apply(lambda s: ", ".join(s.tolist()))
               .rename("depth12_23_players")
               .reset_index()
)

nation_depth = nation_depth.merge(bench_list, on="Nation_code", how="left")

# Sort by depth average score
nation_depth = nation_depth.sort_values(
    ["depth12_23_avg_score", "depth12_23_min_score"], ascending=False
).reset_index(drop=True)

print("Nation Squad Depth computed as mean(players ranked 12–23 by", score_col + ")")
print("Nations with >=1 depth player (rank 12–23):", nation_depth.shape[0])

# Save
out_path_depth = "nation_rankings_squad_depth_12_23_avg.csv"
nation_depth.to_csv(out_path_depth, index=False)
print("Saved:", out_path_depth)


# Compute player-based nation strength as a weighted combo of Starting XI, Star impact, and Squad depth
import numpy as np
import pandas as pd

score_col = "weighted_score_norm2"
base = final_rankings[["Nation_code", "Player", score_col]].copy()

# Rank players within nation by player score (desc)
base["rank_in_nation"] = base.groupby("Nation_code")[score_col].rank(method="first", ascending=False)

# Helper: safe mean
def safe_mean(s: pd.Series) -> float:
    s = pd.to_numeric(s, errors="coerce")
    s = s[np.isfinite(s)]
    return float(s.mean()) if len(s) else np.nan

# Compute components per nation
components = []
for nation, g in base.groupby("Nation_code"):
    g = g.sort_values(score_col, ascending=False)

    top11_mean = safe_mean(g.head(11)[score_col])
    top3_mean = safe_mean(g.head(3)[score_col])

    # Depth: ranks 12-23 inclusive (may be empty)
    depth = g[(g["rank_in_nation"] >= 12) & (g["rank_in_nation"] <= 23)]
    depth_mean = safe_mean(depth[score_col])

    player_based_score = 0.50 * top11_mean + 0.25 * top3_mean + 0.25 * depth_mean

    components.append({
        "Nation_code": nation,
        "n_players": int(len(g)),
        "top11_mean": top11_mean,
        "top3_mean": top3_mean,
        "depth12_23_mean": depth_mean,
        "player_based_score": player_based_score,
    })

player_based_nation_strength = pd.DataFrame(components)
player_based_nation_strength = player_based_nation_strength.sort_values("player_based_score", ascending=False).reset_index(drop=True)

print("Player-based nation strength computed using:")
print("0.50*mean(top11) + 0.25*mean(top3) + 0.25*mean(ranks 12-23)")
print("Note: nations with <23 players may have NaN depth; those will yield NaN player_based_score unless handled.")

out_path = "nation_player_based_strength_weighted_50_25_25.csv"
player_based_nation_strength.to_csv(out_path, index=False)
print("Saved:", out_path)


# Prepare nation strength features for pairwise logistic-regression matchup modeling
import numpy as np
import pandas as pd
from itertools import combinations
from sklearn.linear_model import LogisticRegression

# Base nation strength table computed earlier
pb = player_based_nation_strength.copy()

# Keep only nations in allowed list (by Nation_code available in pb)
# Note: allowed_country_names are names; pb is Nation_code. We'll use Nation_code list present in pb.

# Feature columns (numeric) from pb
feature_cols_pb = [
    "top11_mean",
    "top3_mean",
    "depth12_23_mean",
    "player_based_score",
]

# Coerce numeric
for c in feature_cols_pb:
    pb[c] = pd.to_numeric(pb[c], errors="coerce")

# Drop nations where key feature is missing (depth can be NaN for small nations)
# We'll keep rows with player_based_score present; for depth NaN we can impute later if needed.
print("player_based_nation_strength shape:", pb.shape)
print("Missing rates:")
print(pb[feature_cols_pb].isna().mean().sort_values(ascending=False))

# Build all unordered matchups (A,B) from available nations
nations = pb["Nation_code"].dropna().unique().tolist()
matchups = list(combinations(sorted(nations), 2))
matchups_df = pd.DataFrame(matchups, columns=["team_A", "team_B"])

# Merge features for A and B
A = pb[["Nation_code"] + feature_cols_pb].rename(columns={"Nation_code": "team_A"})
B = pb[["Nation_code"] + feature_cols_pb].rename(columns={"Nation_code": "team_B"})
matchups_df = matchups_df.merge(A, on="team_A", how="left", suffixes=(None, None))
matchups_df = matchups_df.merge(B, on="team_B", how="left", suffixes=("_A", "_B"))

# Ensure suffixes are correct
# After merges, columns will be: team_A, team_B, top11_mean, ... then top11_mean_B etc depending on pandas behavior.
# We'll standardize to explicit _A/_B names.
rename_map = {}
for c in feature_cols_pb:
    if c in matchups_df.columns:
        rename_map[c] = c + "_A"
    if c + "_B" in matchups_df.columns:
        # already ok
        pass
    elif c in matchups_df.columns and c + "_A" not in matchups_df.columns:
        pass
matchups_df = matchups_df.rename(columns=rename_map)

# If B columns didn't get _B suffix due to name collision rules, fix them
for c in feature_cols_pb:
    if c in matchups_df.columns and c + "_A" in matchups_df.columns:
        # ambiguous; skip
        pass

# Create difference features (A - B)
for c in feature_cols_pb:
    ca, cb = c + "_A", c + "_B"
    if ca in matchups_df.columns and cb in matchups_df.columns:
        matchups_df[c + "_diff"] = matchups_df[ca] - matchups_df[cb]

diff_cols = [c + "_diff" for c in feature_cols_pb if c + "_diff" in matchups_df.columns]
print("Matchups:", len(matchups_df), "| diff feature cols:", diff_cols)

print("\nNOTE: To fit LogisticRegression we need historical match outcomes (a target y indicating whether team_A beat team_B).\n"
      "If you provide a match results dataset or specify a proxy target (e.g., higher ELO wins), we can train and then output win probabilities for all pairings.")


# Create a proxy-trained logistic regression model and compute head-to-head win probabilities
# NOTE: Without historical match results, we train on a proxy label: team_A wins if its player_based_score > team_B.
# This produces a smooth probability mapping of strength-differences, NOT an empirically validated win model.

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

# Start from matchups_df created earlier (all combinations) and pb (nation strength features)
req_diff_cols = [
    'top11_mean_diff',
    'top3_mean_diff',
    'depth12_23_mean_diff',
    'player_based_score_diff',
]

# Use the most complete subset for modeling
model_df = matchups_df.copy()

# Keep rows where core diff features are available
# Depth and player_based_score can be NaN for nations with <23 eligible players.
# We'll fit on rows with non-missing player_based_score_diff and top11/top3 diffs.
core = ['top11_mean_diff', 'top3_mean_diff', 'player_based_score_diff']
model_df = model_df.dropna(subset=core).copy()

# If depth is missing, set it to 0 difference (equivalent depth signal absent)
if 'depth12_23_mean_diff' in model_df.columns:
    model_df['depth12_23_mean_diff'] = model_df['depth12_23_mean_diff'].fillna(0.0)

X = model_df[req_diff_cols].astype(float)

# Proxy target: A wins if player_based_score_diff > 0
# (ties -> 0)
y = (model_df['player_based_score_diff'] > 0).astype(int)

# Fit logistic regression (no regularization tuning here; keep interpretable)
clf = LogisticRegression(max_iter=500, solver='lbfgs')
clf.fit(X, y)

# Compute probabilities for ALL matchups (including ones with missing depth diff)
pred_df = matchups_df.copy()
pred_df = pred_df.dropna(subset=core).copy()
if 'depth12_23_mean_diff' in pred_df.columns:
    pred_df['depth12_23_mean_diff'] = pred_df['depth12_23_mean_diff'].fillna(0.0)

Xp = pred_df[req_diff_cols].astype(float)

pA = clf.predict_proba(Xp)[:, 1]
pred_df['P_team_A_wins'] = pA
pred_df['P_team_B_wins'] = 1 - pA

# Make a tidy output
matchup_probs = (
    pred_df[['team_A','team_B','P_team_A_wins','P_team_B_wins'] + req_diff_cols]
    .sort_values('P_team_A_wins', ascending=False)
    .reset_index(drop=True)
)

print('LogisticRegression trained on proxy target: team_A wins if player_based_score_A > player_based_score_B')
print('Training rows used:', len(model_df), 'out of', len(matchups_df))
print('Coefficients (higher -> increases P(team_A wins))')
coef = pd.Series(clf.coef_.ravel(), index=req_diff_cols).sort_values(ascending=False)

print('\nTop 20 most lopsided matchups (by P_team_A_wins):')

# Save
out_path = 'nation_matchup_probabilities_proxy_logreg.csv'
matchup_probs.to_csv(out_path, index=False)
print('Saved:', out_path)


# Recompute matchup probabilities for ALL nation pairings by imputing missing depth and player_based_score
import numpy as np
import pandas as pd
from itertools import permutations

# Start from player_based_nation_strength
pb_full = player_based_nation_strength.copy()

# Impute missing depth with 0 (no evidence of depth); then recompute player_based_score where missing
# player_based_score = 0.50*top11_mean + 0.25*top3_mean + 0.25*depth12_23_mean
pb_full["depth12_23_mean"] = pd.to_numeric(pb_full["depth12_23_mean"], errors="coerce").fillna(0.0)
for c in ["top11_mean", "top3_mean"]:
    pb_full[c] = pd.to_numeric(pb_full[c], errors="coerce")

pb_full["player_based_score_imputed"] = (
    0.50 * pb_full["top11_mean"] +
    0.25 * pb_full["top3_mean"] +
    0.25 * pb_full["depth12_23_mean"]
)

# Use imputed score for matchup features
feature_cols_pb2 = ["top11_mean", "top3_mean", "depth12_23_mean", "player_based_score_imputed"]

# All ordered permutations A vs B (A!=B)
teams = sorted(pb_full["Nation_code"].dropna().unique().tolist())
perm = [(a, b) for a, b in permutations(teams, 2)]
matchups_all = pd.DataFrame(perm, columns=["team_A", "team_B"])

A2 = pb_full[["Nation_code"] + feature_cols_pb2].rename(columns={"Nation_code": "team_A"})
B2 = pb_full[["Nation_code"] + feature_cols_pb2].rename(columns={"Nation_code": "team_B"})

matchups_all = matchups_all.merge(A2, on="team_A", how="left")
matchups_all = matchups_all.merge(B2, on="team_B", how="left", suffixes=("_A", "_B"))

# Difference features (A - B), aligned with training columns in clf
# Difference features (A - B)
# NOTE: because of the merge order + suffixes, team_A columns end with _A and team_B columns end with _B.
matchups_all["top11_mean_diff"] = matchups_all["top11_mean_A"] - matchups_all["top11_mean_B"]
matchups_all["top3_mean_diff"] = matchups_all["top3_mean_A"] - matchups_all["top3_mean_B"]
matchups_all["depth12_23_mean_diff"] = matchups_all["depth12_23_mean_A"] - matchups_all["depth12_23_mean_B"]
matchups_all["player_based_score_diff"] = (
    matchups_all["player_based_score_imputed_A"] - matchups_all["player_based_score_imputed_B"]
)

# Predict with the existing trained LogisticRegression (clf) from cell 19
X_all = matchups_all[[
    "top11_mean_diff",
    "top3_mean_diff",
    "depth12_23_mean_diff",
    "player_based_score_diff",
]].astype(float)

pA_all = clf.predict_proba(X_all)[:, 1]
matchups_all["P_team_A_wins"] = pA_all
matchups_all["P_team_B_wins"] = 1 - pA_all

matchup_probs_all = (
    matchups_all[["team_A", "team_B", "P_team_A_wins", "P_team_B_wins"]]
    .sort_values(["P_team_A_wins"], ascending=False)
    .reset_index(drop=True)
)

print("All ordered matchups:", len(matchup_probs_all), "(should be n*(n-1)) with n=", len(teams))
print("Columns present (sanity check):", [c for c in ["top11_mean_A","top11_mean_B","player_based_score_imputed_A","player_based_score_imputed_B"] if c in matchups_all.columns])

out_path_all = "nation_matchup_probabilities_proxy_logreg_ALL_pairs.csv"
matchup_probs_all.to_csv(out_path_all, index=False)
print("Saved:", out_path_all)




# Diagnose why matchup probabilities saturate at 0/1
import numpy as np
import pandas as pd

# Use the full ordered matchups (built in cell 20)
assert 'matchups_all' in globals() and isinstance(matchups_all, pd.DataFrame)

# Compute logit (decision function) and probability summary
X_all = matchups_all[[
    "top11_mean_diff",
    "top3_mean_diff",
    "depth12_23_mean_diff",
    "player_based_score_diff",
]].astype(float)

logit = clf.decision_function(X_all)
proba = clf.predict_proba(X_all)[:, 1]

print("Predicted probability summary:")
print(pd.Series(proba).describe(percentiles=[0.001, 0.01, 0.05, 0.5, 0.95, 0.99, 0.999]))

print("\nDecision function (logit) summary:")
print(pd.Series(logit).describe(percentiles=[0.001, 0.01, 0.05, 0.5, 0.95, 0.99, 0.999]))

# Count how many are extremely close to 0 or 1
print("\nShare near 0 (<=1%):", float((proba <= 0.01).mean()))
print("Share near 1 (>=99%):", float((proba >= 0.99).mean()))

# Inspect feature scale
print("\nDiff feature scale snapshot:")
desc = X_all.describe(percentiles=[0.01,0.05,0.5,0.95,0.99]).T
print(desc[["mean","std","min","1%","5%","50%","95%","99%","max"]])


# Refit logistic regression on standardized matchup diff features to avoid 0/1 saturation
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

# Use matchups_all (ordered pairs) and the earlier proxy label rule
X_cols = [
    "top11_mean_diff",
    "top3_mean_diff",
    "depth12_23_mean_diff",
    # player_based_score_diff is a linear combo of the other 3 (with our imputation),
    # so exclude it to reduce redundancy / extreme coefficients.
]

X_train = matchups_all[X_cols].astype(float).copy()

y_train = (matchups_all["player_based_score_diff"] > 0).astype(int)

# Standardize features then fit logistic regression with stronger regularization (smaller C)
cal_clf = Pipeline([
    ("scaler", StandardScaler()),
    ("logreg", LogisticRegression(max_iter=2000, solver="lbfgs", C=0.5))
])
cal_clf.fit(X_train, y_train)

# Predict probabilities for all ordered pairs
pA = cal_clf.predict_proba(X_train)[:, 1]
matchup_probs_all_cal = matchups_all[["team_A", "team_B"]].copy()
matchup_probs_all_cal["P_team_A_wins"] = pA
matchup_probs_all_cal["P_team_B_wins"] = 1 - pA

# Add a rounded percent view for readability
matchup_probs_all_cal["P_team_A_wins_pct"] = (100 * matchup_probs_all_cal["P_team_A_wins"]).round(1)
matchup_probs_all_cal["P_team_B_wins_pct"] = (100 * matchup_probs_all_cal["P_team_B_wins"]).round(1)

# Sort by closest to coinflip to see calibration quality too
matchup_probs_all_cal["abs_diff_from_50"] = (matchup_probs_all_cal["P_team_A_wins"] - 0.5).abs()

print("Calibrated probability summary:")
print(matchup_probs_all_cal["P_team_A_wins"].describe(percentiles=[0.01,0.05,0.5,0.95,0.99]))

print("\nMost lopsided (A strongest):")

print("\nMost even matchups (closest to 50/50):")

out_path = "nation_matchup_probabilities_proxy_logreg_ALL_pairs_calibrated.csv"
matchup_probs_all_cal.drop(columns=["abs_diff_from_50"]).to_csv(out_path, index=False)
print("\nSaved:", out_path)


# Lookup the calibrated head-to-head prediction for Germany vs France (both directions)
import pandas as pd

# Ensure the calibrated matchup table exists
assert "matchup_probs_all_cal" in globals(), "matchup_probs_all_cal not found; run the calibrated matchup cell first."

# Extract the two directed matchups
gef = matchup_probs_all_cal[(matchup_probs_all_cal["team_A"] == "GER") & (matchup_probs_all_cal["team_B"] == "FRA")].copy()
fge = matchup_probs_all_cal[(matchup_probs_all_cal["team_A"] == "FRA") & (matchup_probs_all_cal["team_B"] == "GER")].copy()

out = pd.concat([gef, fge], ignore_index=True)

# Keep only the relevant columns for display
cols = [
    "team_A","team_B",
    "P_team_A_wins","P_team_B_wins",
    "P_team_A_wins_pct","P_team_B_wins_pct",
]
out = out[cols].sort_values(["team_A","team_B"]).reset_index(drop=True)

out