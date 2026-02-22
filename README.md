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

## Data Files Used & Purpose

- **matches (1).csv** — Historical World Cup match results. Used as core training data to learn upset patterns and dark scores. (https://www.kaggle.com/code/sarazahran1/world-cup-2026-match-predictor/input?select=matches.csv)
- **teams_elo.csv** — Elo ratings for each nation. Provides team strength differentials for modeling favorites vs underdogs. (https://www.kaggle.com/code/sarazahran1/world-cup-2026-match-predictor) Used with permission by the owner of the dataset.
- **fc26_players_clean_filled.csv** — Corrected player dataset with missing stats filled. Use this in the API. (Web Scraped from sofifa.com)
- **wc2018_2022_upset_training_filled.csv** — Final combined historical training dataset used to train XGBoost. (Web Scraped from sofifa.com)
- **wc2018_2022_model_matrix.csv** — Fully numeric feature matrix for model input.
- **group_stage_probabilities.csv** — Predicted match win/upset probabilities for the 2026 group stage. Use as training data to learn about upset patterns and dark scores.
- **group_standings (1).csv** — Simulated final group standings. Use as training data to learn about upset patterns and dark scores.

## Sphinx Usage

- Use Sphinx to assist with the engineering of our formula called the Darkscore, which quantifies a team’s upset potential using historical match data, Elo differentials, and FC26 team aggregate features.
**Feature Sources:**
- Pace / Physical / Defensive metrics → `fc26_team_aggregates.csv`
- Potential Gap / Volatility → Player-derived aggregates
- Elo Differential → `teams_elo.csv`
- Historical upset calibration → `matches (1).csv`

Higher DarkScore = higher upset likelihood.

Additionally, Sphinx was used as a way to implement visualizations for individual player stats using six axes directly on our frontend:

- Pace  
- Shooting  
- Passing  
- Dribbling  
- Defending  
- Physical  

These radar plots provide a visual comparison of player strengths and support frontend storytelling for upset candidates.


