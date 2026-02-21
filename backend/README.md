# Backend (FastAPI)

## Run locally

```bash
cd backend
python -m venv .venv
(or: python3 -m venv .venv)
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Optional env var:

- `MATCHUP_CSV_PATH` (override default `backend/data/nation_matchup_probabilities_proxy_logreg_ALL_pairs_calibrated.csv`)
- `CORS_ALLOW_ORIGINS` (comma-separated exact origins, e.g. `https://app.example.com`)
- `CORS_ALLOW_ORIGIN_REGEX` (regex fallback for allowed origins)

## Endpoints

- `GET /health`
- `GET /teams`
- `POST /predict-matchup`

Example request body:

```json
{
  "team_a": "Germany",
  "team_b": "Morocco",
  "neutral_site": true,
  "tournament_stage": "group"
}
```
