from __future__ import annotations

import csv
from pathlib import Path

MATCHUP_TABLE_FILENAME = "nation_matchup_probabilities_proxy_logreg_ALL_pairs_calibrated.csv"

# Full team name -> nation code used in the model CSV.
NAME_TO_CODE: dict[str, str] = {
    "Canada": "CAN",
    "Mexico": "MEX",
    "United States": "USA",
    "Australia": "AUS",
    "Iran": "IRN",
    "Japan": "JPN",
    "Jordan": "JOR",
    "South Korea": "KOR",
    "Qatar": "QAT",
    "Saudi Arabia": "KSA",
    "Uzbekistan": "UZB",
    "Algeria": "ALG",
    "Cape Verde": "CPV",
    "Egypt": "EGY",
    "Ghana": "GHA",
    "Ivory Coast": "CIV",
    "Morocco": "MAR",
    "Senegal": "SEN",
    "South Africa": "RSA",
    "Tunisia": "TUN",
    "Cura\u00e7ao": "CUW",
    "Curacao": "CUW",
    "Haiti": "HAI",
    "Panama": "PAN",
    "Argentina": "ARG",
    "Brazil": "BRA",
    "Colombia": "COL",
    "Ecuador": "ECU",
    "Paraguay": "PAR",
    "Uruguay": "URU",
    "New Zealand": "NZL",
    "Austria": "AUT",
    "Belgium": "BEL",
    "Croatia": "CRO",
    "England": "ENG",
    "France": "FRA",
    "Germany": "GER",
    "Netherlands": "NED",
    "Norway": "NOR",
    "Portugal": "POR",
    "Scotland": "SCO",
    "Spain": "ESP",
    "Switzerland": "SUI",
}


def default_matchup_csv_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / MATCHUP_TABLE_FILENAME


def load_matchup_lookup(csv_path: Path) -> dict[tuple[str, str], float]:
    """Load directed matchup win probabilities keyed by (team_A_code, team_B_code)."""
    with csv_path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.DictReader(csv_file)
        required = {"team_A", "team_B", "P_team_A_wins"}
        fieldnames = set(reader.fieldnames or [])
        missing = required - fieldnames
        if missing:
            missing_fields = ", ".join(sorted(missing))
            raise ValueError(f"Matchup CSV missing required columns: {missing_fields}")

        lookup: dict[tuple[str, str], float] = {}
        for row in reader:
            team_a = row["team_A"].strip().upper()
            team_b = row["team_B"].strip().upper()
            if not team_a or not team_b:
                continue
            lookup[(team_a, team_b)] = float(row["P_team_A_wins"])

    if not lookup:
        raise ValueError(f"No matchup rows loaded from {csv_path}")
    return lookup


def extract_supported_codes(lookup: dict[tuple[str, str], float]) -> set[str]:
    supported: set[str] = set()
    for team_a, team_b in lookup:
        supported.add(team_a)
        supported.add(team_b)
    return supported


def resolve_team_code(team_name: str) -> str | None:
    return NAME_TO_CODE.get(team_name.strip())

