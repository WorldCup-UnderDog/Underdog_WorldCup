"""Load and normalize model and roster data files."""

from __future__ import annotations

import csv
import logging
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

TEAM_TO_CODE = {
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
    "Curaçao": "CUW",
    "Ecuador": "ECU",
    "Egypt": "EGY",
    "England": "ENG",
    "France": "FRA",
    "Germany": "GER",
    "Ghana": "GHA",
    "Haiti": "HAI",
    "Iran": "IRN",
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

CODE_TO_TEAM = {value: key for key, value in TEAM_TO_CODE.items()}

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = REPO_ROOT / "backend"
DATA_ROOT = BACKEND_ROOT / "data"
SERVICE_DATA_ROOT = Path(__file__).resolve().parent / "Cleaned_Data"


@dataclass(frozen=True)
class MatchupDataset:
    teams: list[str]
    probabilities: dict[tuple[str, str], tuple[float, float]]
    team_strength: dict[str, float]
    team_elo: dict[str, float]
    source_file: str
    fallback_source_file: str


@dataclass(frozen=True)
class PlayerRecord:
    name: str
    nation: str
    best_position: str
    club: str
    overall_rating: str
    potential: str
    age: str


def normalize_text(value: str) -> str:
    raw = unicodedata.normalize("NFKD", str(value or ""))
    ascii_value = raw.encode("ascii", "ignore").decode("ascii")
    return " ".join(ascii_value.lower().strip().split())


def _resolve_data_file(name: str) -> Path:
    candidates = [
        DATA_ROOT / name,
        BACKEND_ROOT / name,
        REPO_ROOT / name,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not locate data file '{name}'. Checked: {', '.join(str(p) for p in candidates)}")


def _resolve_elo_file() -> Path:
    candidates = [
        SERVICE_DATA_ROOT / "teams_elo.csv",
        DATA_ROOT / "teams_elo.csv",
        BACKEND_ROOT / "teams_elo.csv",
        REPO_ROOT / "teams_elo.csv",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not locate teams_elo.csv. Checked: {', '.join(str(p) for p in candidates)}")


def _to_float(raw: str, fallback: float) -> float:
    text = str(raw or "").strip()
    if not text:
        return fallback
    try:
        return float(text)
    except ValueError:
        return fallback


def _normalize_team_key(value: str) -> str:
    text = str(value or "").replace("_", " ").replace("-", " ")
    return normalize_text(text)


def _team_lookup() -> dict[str, str]:
    team_by_key = {_normalize_team_key(team): team for team in TEAM_TO_CODE}
    team_by_key.update(
        {
            _normalize_team_key("Côte d’Ivoire"): "Ivory Coast",
            _normalize_team_key("Cote d'Ivoire"): "Ivory Coast",
            _normalize_team_key("Cote dIvoire"): "Ivory Coast",
            _normalize_team_key("Ivory_Coast"): "Ivory Coast",
            _normalize_team_key("Cape_Verde"): "Cape Verde",
            _normalize_team_key("Curacao"): "Curaçao",
            _normalize_team_key("Korea Republic"): "South Korea",
            _normalize_team_key("USA"): "United States",
        }
    )
    return team_by_key


def _load_teams_elo() -> tuple[dict[str, float], str]:
    csv_path = _resolve_elo_file()
    team_by_key = _team_lookup()

    latest_by_team: dict[str, tuple[datetime | None, float]] = {}
    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            team_raw = row.get("team", "")
            canonical_team = team_by_key.get(_normalize_team_key(team_raw))
            if not canonical_team:
                continue

            elo = _to_float(row.get("elo"), fallback=-1)
            if elo <= 0:
                continue

            date_raw = str(row.get("date", "")).strip()
            parsed_date = None
            if date_raw:
                try:
                    parsed_date = datetime.fromisoformat(date_raw)
                except ValueError:
                    parsed_date = None

            previous = latest_by_team.get(canonical_team)
            if previous is None:
                latest_by_team[canonical_team] = (parsed_date, elo)
                continue

            prev_date, _ = previous
            if parsed_date is None:
                continue
            if prev_date is None or parsed_date >= prev_date:
                latest_by_team[canonical_team] = (parsed_date, elo)

    team_elo = {team: value for team, (_, value) in latest_by_team.items()}
    logger.info("Loaded external Elo table: teams=%s source=%s", len(team_elo), csv_path.name)
    return team_elo, csv_path.name


def _load_team_strength_from_fc26() -> dict[str, float]:
    csv_path = _resolve_data_file("fc26_combined.csv")
    by_team: dict[str, list[float]] = {team: [] for team in TEAM_TO_CODE}
    team_by_key = _team_lookup()

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            nation_key = _normalize_team_key(row.get("nation", ""))
            matched_team = team_by_key.get(nation_key)
            if not matched_team:
                continue
            overall = _to_float(row.get("overall_rating"), fallback=-1)
            if overall < 0:
                continue
            by_team[matched_team].append(overall)

    strength: dict[str, float] = {}
    fallback_pool = []
    for team, values in by_team.items():
        if not values:
            continue
        top = sorted(values, reverse=True)[:11]
        team_strength = sum(top) / len(top)
        strength[team] = team_strength
        fallback_pool.append(team_strength)

    default_strength = sum(fallback_pool) / len(fallback_pool) if fallback_pool else 70.0
    for team in TEAM_TO_CODE:
        strength.setdefault(team, default_strength)

    logger.info("Loaded team strength priors: teams=%s source=%s", len(strength), csv_path.name)
    return strength


def load_matchup_dataset() -> MatchupDataset:
    csv_path = _resolve_data_file("nation_matchup_probabilities_proxy_logreg_ALL_pairs_calibrated.csv")
    probabilities: dict[tuple[str, str], tuple[float, float]] = {}
    team_strength = _load_team_strength_from_fc26()
    team_elo, elo_source = _load_teams_elo()

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            code_a = str(row.get("team_A", "")).strip().upper()
            code_b = str(row.get("team_B", "")).strip().upper()
            team_a = CODE_TO_TEAM.get(code_a)
            team_b = CODE_TO_TEAM.get(code_b)
            if not team_a or not team_b:
                continue

            prob_a = _to_float(row.get("P_team_A_wins"), 0.5)
            prob_b = _to_float(row.get("P_team_B_wins"), 0.5)
            total = prob_a + prob_b
            if total <= 0:
                prob_a, prob_b = 0.5, 0.5
            else:
                prob_a, prob_b = prob_a / total, prob_b / total

            probabilities[(team_a, team_b)] = (prob_a, prob_b)
    if not probabilities:
        raise RuntimeError(f"No matchup probabilities loaded from {csv_path}")

    sorted_teams = sorted(TEAM_TO_CODE.keys())
    logger.info(
        "Loaded matchup matrix: supported_teams=%s matrix_pairs=%s source=%s",
        len(sorted_teams),
        len(probabilities),
        csv_path.name,
    )
    return MatchupDataset(
        teams=sorted_teams,
        probabilities=probabilities,
        team_strength=team_strength,
        team_elo=team_elo,
        source_file=elo_source,
        fallback_source_file=csv_path.name,
    )


def load_player_records() -> list[PlayerRecord]:
    csv_path = _resolve_data_file("fc26_combined.csv")
    players: list[PlayerRecord] = []

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            nation_raw = str(row.get("nation", "")).strip()
            normalized_nation = normalize_text(nation_raw)
            canonical_nation = next(
                (team for team in TEAM_TO_CODE if normalize_text(team) == normalized_nation),
                nation_raw.title() if nation_raw else "Unknown",
            )

            players.append(
                PlayerRecord(
                    name=str(row.get("name", "")).strip() or "Data missing",
                    nation=canonical_nation,
                    best_position=str(row.get("best_position", "")).strip() or "Data missing",
                    club=str(row.get("team_contract", "")).strip() or "Data missing",
                    overall_rating=str(row.get("overall_rating", "")).strip() or "Data missing",
                    potential=str(row.get("potential", "")).strip() or "Data missing",
                    age=str(row.get("age", "")).strip() or "Data missing",
                )
            )

    logger.info("Loaded player records: count=%s source=%s", len(players), csv_path.name)
    return players
