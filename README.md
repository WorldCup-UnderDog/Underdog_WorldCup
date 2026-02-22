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

## Deploy (Vercel + Render)

### Frontend (Vercel)

1. Import this repo in Vercel.
2. Set environment variables in Vercel project settings:
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_ANON_KEY`
   - `VITE_API_BASE_URL=https://<your-render-service>.onrender.com`
3. Deploy from `main`.

Notes:
- `vercel.json` includes SPA rewrites so deep links like `/app/matchup` work.

### Backend (Render)

1. Create a new Web Service from this repo on Render.
2. Render can read `render.yaml` for:
   - `buildCommand: pip install -r backend/requirements.txt`
   - `startCommand: uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`
3. Set environment variables:
   - `APP_ENV=production`
   - `DEBUG=false`
   - `CORS_ORIGINS=https://<your-vercel-domain>`

Notes:
- Backend CORS is environment-driven via `CORS_ORIGINS`.

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
