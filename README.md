# Underdog World Cup

Underdog World Cup is a React (Vite) app with Supabase auth.

Current app pages:
- React (Vite) UI
- Supabase auth
- Matchup tool at `/app/matchup`
- Team roster overview at `/app/rosters`
- Team roster detail at `/app/rosters/:team`

## Repo Layout

- `src/` frontend app

## Local Setup

```bash
npm install
npm run dev
```

## Environment Variables

Create `.env` in the repo root:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_API_BASE_URL` (optional, used only if you connect the matchup page to an external API)

## Notes

- The backend project has been removed from this repo.
