const BASE_URL = "http://localhost:8000";

export async function fetchMatchProbability(teamA, teamB) {
  const res = await fetch(`${BASE_URL}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ team_a: teamA, team_b: teamB }),
  });
  return res.json();
}

export async function fetchUpsetScore(teamA, teamB, scoreA, scoreB) {
  const res = await fetch(`${BASE_URL}/upset`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ team_a: teamA, team_b: teamB, score_a: scoreA, score_b: scoreB }),
  });
  return res.json();
}


export async function fetchPlayersByNation(nation) {
  const res = await fetch(`${BASE_URL}/players/${nation}`);
  return res.json();
}

export async function fetchTopUpsetPlayers() {
  const res = await fetch(`${BASE_URL}/players/top-upsets`);
  return res.json();
}

export async function fetchGKWallRanking() {
  const res = await fetch(`${BASE_URL}/goalkeepers/wall-ranking`);
  return res.json();
}


export async function fetchPlayers(nation = null, position = null) {
  const params = new URLSearchParams();
  if (nation) params.append("nation", nation);
  if (position) params.append("position", position);
  const res = await fetch(`${BASE_URL}/players?${params}`);
  return res.json();
}

export async function fetchPlayer(name) {
  const res = await fetch(`${BASE_URL}/player/${encodeURIComponent(name)}`);
  return res.json();
}