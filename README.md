# Underdog World Cup

Underdog World Cup is a React (Vite) frontend with Supabase auth and a FastAPI backend for prediction APIs.

## App Pages

- Matchup tool at `/app/matchup`
- Team roster overview at `/app/rosters`
- Team roster detail at `/app/rosters/:team`
- Profile and dashboard pages (Supabase-authenticated)

## Repo Layout

- `src/` frontend app
- `backend/app/` FastAPI application
- `backend/data/` model + player datasets used by the API
- `public/data/` generated static roster artifacts used by frontend roster views

## Local Setup

### Frontend

```bash
npm install
npm run dev
```

### Backend

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
backend/.venv/bin/python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

## Environment Variables

Create `.env` in the repo root:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_API_BASE_URL` (default expected by frontend: `http://localhost:8000`)

Backend env example:

- `backend/.env.example`

## Backend Endpoints

- `GET /health`
- `GET /teams`
- `POST /predict-matchup`
- `POST /predict` (legacy alias)
- `POST /upset`
- `GET /players/{nation}`
- `GET /players/top-upsets`
- `GET /goalkeepers/wall-ranking`

Versioned aliases are also available under `/api/v1/*`.

For backend-specific notes, see `backend/README.md`.
