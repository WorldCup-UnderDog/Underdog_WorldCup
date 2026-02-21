# Backend (FastAPI)

## Run locally

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Endpoints

- `GET /health`
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
