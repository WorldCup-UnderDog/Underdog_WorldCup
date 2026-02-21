# Underdog World Cup

Underdog World Cup is a React + FastAPI app for matchup probability predictions.

Frontend:
- React (Vite) UI
- Supabase auth
- Matchup tool at `/app/matchup`

Backend:
- FastAPI API
- CSV-backed matchup probability lookup
- Team support endpoint used by the frontend dropdowns

## Repo Layout

- `src/` frontend app
- `backend/app/` FastAPI app
- `backend/app/services/` model lookup and prediction logic
- `backend/data/` model CSV files used at runtime

## Local Setup

### 1. Frontend

```bash
npm install
npm run dev
```

### 2. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## Environment Variables

Create `.env` in the repo root:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_API_BASE_URL` (optional, defaults to `http://localhost:8000`)

Backend optional vars are documented in `backend/.env.example`:
- `MATCHUP_CSV_PATH`
- `CORS_ALLOW_ORIGINS`
- `CORS_ALLOW_ORIGIN_REGEX`

## API Endpoints

- `GET /health`
  - Returns service status and loaded matchup metadata.
- `GET /teams`
  - Returns model-supported team names for the frontend selector.
- `POST /predict-matchup`
  - Request body:

```json
{
  "team_a": "Germany",
  "team_b": "Morocco",
  "neutral_site": true
}
```

## Notes

- The matchup UI fetches team options from `/teams` on load.
- If `/teams` fails, the UI falls back to a default local team list and shows an error banner.
- Run both frontend and backend during local development.
