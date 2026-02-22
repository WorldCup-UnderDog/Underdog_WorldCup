import pandas as pd
import sys
import os

CSV_PATH = "/Users/arjunramakrishnan/IdeaProjects/Underdog_WorldCup/backend/data/fc26_combined.csv"  # update path if needed

POS_GROUPS = {
    "1": ("GK",  ["GK"]),
    "2": ("DEF", ["CB", "LB", "RB", "LWB", "RWB"]),
    "3": ("MID", ["CM", "CDM", "CAM", "LM", "RM"]),
    "4": ("FWD", ["ST", "CF", "LW", "RW"]),
}

NATIONS = [
    "algeria","argentina","australia","austria","belgium","brazil","canada","cape verde",
    "colombia","croatia","curacao","ecuador","egypt","england","france","germany","ghana",
    "haiti","iran","ivory coast","japan","jordan","mexico","morocco","netherlands",
    "new zealand","norway","panama","paraguay","portugal","qatar","saudi arabia","scotland",
    "senegal","south africa","south korea","spain","switzerland","tunisia","united states",
    "uruguay","uzbekistan",
]

def load_data():
    if not os.path.exists(CSV_PATH):
        print(f"\n  ✗ Could not find '{CSV_PATH}'. Update CSV_PATH in the script.\n")
        sys.exit(1)
    df = pd.read_csv(CSV_PATH)
    df = df[df["name"].notna() & df["overall_rating"].notna()]
    return df

def divider(char="─", width=52):
    print(char * width)

def header(title):
    divider("━")
    print(f"  {title}")
    divider("━")

def section(title):
    print(f"\n  ── {title}")
    divider("─")

def stat_bar(label, value, width=20):
    if value is None or pd.isna(value):
        print(f"  {label:<20}  —")
        return
    v = int(value)
    filled = round((v / 100) * width)
    bar = "█" * filled + "░" * (width - filled)
    print(f"  {label:<20}  {bar}  {v}")

def cat_bar(label, value, max_val=500, width=20):
    if value is None or pd.isna(value):
        print(f"  {label:<20}  —")
        return
    v = int(value)
    pct = min(v / max_val, 1.0)
    filled = round(pct * width)
    bar = "█" * filled + "░" * (width - filled)
    print(f"  {label:<20}  {bar}  {v}")

def print_profile(row):
    is_gk = str(row.get("best_position", "")).strip().upper() == "GK"

    overall   = row.get("overall_rating")
    potential = row.get("potential")
    gap       = int(potential - overall) if pd.notna(potential) and pd.notna(overall) else None
    age       = row.get("age")
    value     = row.get("value", "—")
    nation    = str(row.get("nation", "—")).title()
    position  = row.get("best_position", "—")

    playstyles = [
        str(row.get(c, "")).strip()
        for c in ["playstyles","playstyles2","playstyles3","playstyles4","playstyles5"]
        if pd.notna(row.get(c)) and str(row.get(c, "")).strip()
    ]

    # ── Header ────────────────────────────────────────────
    print()
    header(f"  {row['name'].upper()}  {'[GK]' if is_gk else ''}")
    print(f"  Nation:    {nation}")
    print(f"  Position:  {position}")
    print()

    # ── Ratings ──────────────────────────────────────────
    section("RATINGS")
    print(f"  {'Overall':<16}  {int(overall) if pd.notna(overall) else '—'}")
    print(f"  {'Potential':<16}  {int(potential) if pd.notna(potential) else '—'}")
    gap_str = (f"+{gap}" if gap > 0 else str(gap)) if gap is not None else "—"
    print(f"  {'Growth Gap':<16}  {gap_str}")
    print(f"  {'Age':<16}  {int(age) if pd.notna(age) else '—'}")
    print(f"  {'Market Value':<16}  {value}")

    # ── Playstyles ────────────────────────────────────────
    if playstyles:
        section("PLAYSTYLES")
        for ps in playstyles:
            print(f"  •  {ps}")

    # ── Key Attributes ────────────────────────────────────
    if is_gk:
        section("KEY GK ATTRIBUTES")
        gk_total = row.get("total_goalkeeping")
        gk_ability = min(round(float(gk_total) / 5), 100) if pd.notna(gk_total) else None
        stat_bar("GK Ability",    gk_ability)
        stat_bar("Reactions",     row.get("reactions"))
        stat_bar("Handling",      row.get("ball_control"))
        stat_bar("Kicking",       row.get("long_passing"))
        stat_bar("Aerial Reach",  row.get("heading_accuracy"))
    else:
        section("KEY ATTRIBUTES")
        stat_bar("Acceleration",  row.get("acceleration"))
        stat_bar("Sprint Speed",  row.get("sprint_speed"))
        stat_bar("Dribbling",     row.get("dribbling"))
        stat_bar("Finishing",     row.get("finishing"))
        stat_bar("Short Passing", row.get("short_passing"))

    # ── Hexagon Radar (text) ──────────────────────────────
    if is_gk:
        section("SAVE PROFILE RADAR  (6 axes)")
        gk_total = row.get("total_goalkeeping")
        gk_ability = min(round(float(gk_total) / 5), 100) if pd.notna(gk_total) else None
        sp = row.get("short_passing"); lp = row.get("long_passing")
        dist = round((float(sp) + float(lp)) / 2) if pd.notna(sp) and pd.notna(lp) else None
        stat_bar("GK Ability",    gk_ability)
        stat_bar("Reactions",     row.get("reactions"))
        stat_bar("Distribution",  dist)
        stat_bar("Sweeping",      row.get("sprint_speed"))
        stat_bar("Aerial",        row.get("heading_accuracy"))
        stat_bar("Positioning",   row.get("acceleration"))
    else:
        section("ATTRIBUTE RADAR  (6 axes)")
        ac = row.get("acceleration"); ss = row.get("sprint_speed")
        pace = round((float(ac) + float(ss)) / 2) if pd.notna(ac) and pd.notna(ss) else None
        sp = row.get("short_passing"); lp = row.get("long_passing")
        passing = round((float(sp) + float(lp)) / 2) if pd.notna(sp) and pd.notna(lp) else None
        td = row.get("total_defending")
        defending = min(round(float(td) / 5), 100) if pd.notna(td) else None
        tp = row.get("total_power")
        physical = min(round(float(tp) / 5), 100) if pd.notna(tp) else None
        stat_bar("Pace",      pace)
        stat_bar("Shooting",  row.get("finishing"))
        stat_bar("Passing",   passing)
        stat_bar("Dribbling", row.get("dribbling"))
        stat_bar("Defending", defending)
        stat_bar("Physical",  physical)

    # ── Category Totals ───────────────────────────────────
    if is_gk:
        section("GK CATEGORY TOTALS")
        cat_bar("Goalkeeping", row.get("total_goalkeeping"))
        cat_bar("Movement",    row.get("total_movement"))
        cat_bar("Power",       row.get("total_power"))
        cat_bar("Mentality",   row.get("total_mentality"))
    else:
        section("CATEGORY TOTALS")
        cat_bar("Attacking",  row.get("total_attacking"))
        cat_bar("Skill",      row.get("total_skill"))
        cat_bar("Movement",   row.get("total_movement"))
        cat_bar("Power",      row.get("total_power"))
        cat_bar("Mentality",  row.get("total_mentality"))
        cat_bar("Defending",  row.get("total_defending"))

    divider("━")
    print()

def pick_from_list(items, label):
    print(f"\n  {label}:")
    for i, item in enumerate(items, 1):
        print(f"  {i:>3}.  {item}")
    while True:
        raw = input("\n  Enter number: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(items):
            return items[int(raw) - 1]
        print("  Invalid. Try again.")

def main():
    print()
    print("  ╔══════════════════════════════════════════════════╗")
    print("  ║   FIFA WORLD CUP 2026 · PLAYER PROFILE LOOKUP   ║")
    print("  ╚══════════════════════════════════════════════════╝")

    df = load_data()
    df_valid = df.copy()
    df_valid["nation_clean"] = df_valid["nation"].str.lower().str.strip()

    while True:
        # ── Step 1: filter mode ───────────────────────────────
        print("\n  Filter by:")
        print("   1.  Position group  (GK / DEF / MID / FWD)")
        print("   2.  Nation  (country)")
        print("   q.  Quit")

        mode = input("\n  Choose [1/2/q]: ").strip().lower()
        if mode == "q":
            print("\n  Goodbye.\n")
            break

        subset = df_valid.copy()

        # ── Step 2: pick filter value ─────────────────────────
        if mode == "1":
            print("\n  Position groups:")
            for k, (label, _) in POS_GROUPS.items():
                positions = POS_GROUPS[k][1]
                count = len(df_valid[df_valid["best_position"].isin(positions)])
                print(f"   {k}.  {label:<6}  ({count} players)")
            pg = input("\n  Choose [1/2/3/4]: ").strip()
            if pg not in POS_GROUPS:
                print("  Invalid choice.")
                continue
            _, positions = POS_GROUPS[pg]
            subset = subset[subset["best_position"].isin(positions)]

        elif mode == "2":
            print()
            for i, n in enumerate(NATIONS, 1):
                count = len(df_valid[df_valid["nation_clean"] == n])
                print(f"  {i:>3}.  {n.title():<20}  ({count} players)")
            raw = input("\n  Enter nation number: ").strip()
            if not raw.isdigit() or not (1 <= int(raw) <= len(NATIONS)):
                print("  Invalid.")
                continue
            chosen_nation = NATIONS[int(raw) - 1]
            subset = subset[subset["nation_clean"] == chosen_nation]

        else:
            print("  Invalid. Enter 1, 2, or q.")
            continue

        if subset.empty:
            print("  No players found for that filter.")
            continue

        # ── Step 3: search / pick player ─────────────────────
        subset_sorted = subset.sort_values("overall_rating", ascending=False)

        print(f"\n  {len(subset_sorted)} players found. Type part of a name to search (or press Enter to list all):")
        query = input("  Search: ").strip().lower()

        if query:
            results = subset_sorted[subset_sorted["name"].str.lower().str.contains(query, na=False)]
        else:
            results = subset_sorted

        if results.empty:
            print("  No players matched that search.")
            continue

        names = results["name"].tolist()
        chosen_name = pick_from_list(names, "Select a player")

        # ── Output profile ────────────────────────────────────
        player_row = results[results["name"] == chosen_name].iloc[0]
        print_profile(player_row)

        again = input("  Look up another player? [y/n]: ").strip().lower()
        if again != "y":
            print("\n  Goodbye.\n")
            break

if __name__ == "__main__":
    main()