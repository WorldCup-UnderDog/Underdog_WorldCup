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