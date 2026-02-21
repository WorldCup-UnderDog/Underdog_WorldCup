from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="Underdog Matchup API", version="0.1.0")

# Local-dev CORS. Restrict in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
