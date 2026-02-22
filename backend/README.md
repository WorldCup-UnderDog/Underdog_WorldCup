# FastAPI Backend

## Run locally

1. Create a Python virtual environment.
2. Install dependencies:
   - `pip install -r backend/requirements.txt`
3. Start API:
   - `uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000`

## Available endpoints

- `GET /health`
- `GET /teams`
- `POST /predict-matchup`
- `POST /predict` (legacy alias)
- `POST /upset`
- `GET /players/{nation}`
- `GET /players/top-upsets`
- `GET /goalkeepers/wall-ranking`

Versioned aliases are also available under `/api/v1/*`.

