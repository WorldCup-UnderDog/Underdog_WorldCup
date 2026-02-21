from typing import Literal
import sys,os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
from upset_director import load_matchup_table, build_lookup, get_win_prob

app = FastAPI(title="Dark Horse Matchup API", version="0.1.0")


# Local-dev CORS. Restrict in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load once on startup
df = load_matchup_table(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data/nation_matchup_probabilities_proxy_logreg_ALL_pairs_calibrated.csv")
)
lookup = build_lookup(df)

# Full name → nation code (matches your frontend TEAMS list)
NAME_TO_CODE = {
    "Canada": "CAN", "Mexico": "MEX", "United States": "USA",
    "Australia": "AUS", "Iran": "IRN", "Japan": "JPN", "Jordan": "JOR",
    "South Korea": "KOR", "Qatar": "QAT", "Saudi Arabia": "KSA", "Uzbekistan": "UZB",
    "Algeria": "ALG", "Cape Verde": "CPV", "Egypt": "EGY", "Ghana": "GHA",
    "Ivory Coast": "CIV", "Morocco": "MAR", "Senegal": "SEN",
    "South Africa": "RSA", "Tunisia": "TUN",
    "Curaçao": "CUW", "Haiti": "HAI", "Panama": "PAN",
    "Argentina": "ARG", "Brazil": "BRA", "Colombia": "COL", "Ecuador": "ECU",
    "Paraguay": "PAR", "Uruguay": "URU", "New Zealand": "NZL",
    "Austria": "AUT", "Belgium": "BEL", "Croatia": "CRO", "England": "ENG",
    "France": "FRA", "Germany": "GER", "Netherlands": "NED", "Norway": "NOR",
    "Portugal": "POR", "Scotland": "SCO", "Spain": "ESP", "Switzerland": "SUI",
}


class MatchupRequest(BaseModel):
    team_a: str = Field(min_length=2)
    team_b: str = Field(min_length=2)
    neutral_site: bool = True
    tournament_stage: str | None = None


class MatchupResponse(BaseModel):
    team_a: str
    team_b: str
    team_a_win_prob: float
    draw_prob: float
    team_b_win_prob: float
    upset_score: float
    predicted_winner: str
    confidence: Literal["low", "medium", "high"]
    explanation: list[str]


def _real_predict(req: MatchupRequest) -> MatchupResponse:
    code_a = NAME_TO_CODE.get(req.team_a)
    code_b = NAME_TO_CODE.get(req.team_b)

    # Fall back to mock if team not in model
    if not code_a or not code_b:
        return _mock_predict(req)

    p_a, p_b = get_win_prob(code_a, code_b, lookup)

    # Draw probability: higher when teams are evenly matched
    closeness = 1 - abs(p_a - p_b)
    draw = round(closeness * 18, 1)
    win_a = round(p_a * (100 - draw), 1)
    win_b = round(p_b * (100 - draw), 1)

    # Fix rounding to sum to 100
    diff = round(100 - win_a - win_b - draw, 1)
    win_a += diff

    predicted_winner = req.team_a if p_a >= p_b else req.team_b
    underdog = req.team_b if p_a >= p_b else req.team_a
    underdog_prob = min(p_a, p_b)

    # Upset score on 0–10 scale to match your UpsetMeter
    gap = abs(p_a - p_b)
    upset_score = round(max(0.0, min(10.0, 10.0 - (gap * 20))), 1)

    confidence: Literal["low", "medium", "high"] = (
        "high" if gap > 0.25 else "medium" if gap > 0.10 else "low"
    )

    explanation = [
        f"{predicted_winner} has a stronger player-based strength score from our model.",
        f"Starting XI quality favors {predicted_winner} based on top-11 player ratings.",
        f"Win probability: {req.team_a} {win_a}% / Draw {draw}% / {req.team_b} {win_b}%.",
    ]
    if underdog_prob < 0.35:
        explanation.append(f"A win for {underdog} would be a significant upset.")
    if not req.neutral_site:
        explanation.append(f"{req.team_a} has a home advantage factored in.")

    return MatchupResponse(
        team_a=req.team_a,
        team_b=req.team_b,
        team_a_win_prob=win_a,
        draw_prob=draw,
        team_b_win_prob=win_b,
        upset_score=upset_score,
        predicted_winner=predicted_winner,
        confidence=confidence,
        explanation=explanation,
    )


def _mock_predict(req: MatchupRequest) -> MatchupResponse:
    # TODO: Replace with real Python model inference.
    # Contract is stable so frontend can integrate now.
    base_a = (sum(ord(c) for c in req.team_a.lower()) % 35) + 30
    base_b = (sum(ord(c) for c in req.team_b.lower()) % 35) + 30
    draw = 18.0

    total = base_a + base_b
    a_prob = (base_a / total) * (100 - draw)
    b_prob = (base_b / total) * (100 - draw)

    # Simple upset heuristic: closer matchup -> higher upset potential.
    gap = abs(a_prob - b_prob)
    upset_score = round(max(1.0, 10.0 - (gap / 10.0)), 1)

    winner = req.team_a if a_prob >= b_prob else req.team_b
    confidence = "high" if gap >= 20 else "medium" if gap >= 10 else "low"

    return MatchupResponse(
        team_a=req.team_a,
        team_b=req.team_b,
        team_a_win_prob=round(a_prob, 1),
        draw_prob=round(draw, 1),
        team_b_win_prob=round(b_prob, 1),
        upset_score=upset_score,
        predicted_winner=winner,
        confidence=confidence,
        explanation=[
            "Relative team strength and form drive baseline probabilities.",
            "Upset score increases when team strength gap is small.",
            f"Neutral site set to {req.neutral_site}.",
        ],
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict-matchup", response_model=MatchupResponse)
def predict_matchup(req: MatchupRequest) -> MatchupResponse:
    return _mock_predict(req)
