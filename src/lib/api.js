const BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

async function parseErrorMessage(res) {
  const text = await res.text();
  if (!text) return `Request failed (${res.status})`;
  try {
    const parsed = JSON.parse(text);
    return parsed.detail || parsed.message || text;
  } catch {
    return text;
  }
}

export async function apiRequest(path, options = {}) {
  const {
    method = "GET",
    body,
    headers = {},
    query = null,
  } = options;

  const url = new URL(`${BASE_URL}${path}`);
  if (query && typeof query === "object") {
    Object.entries(query).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        url.searchParams.set(key, String(value));
      }
    });
  }

  const requestHeaders = { ...headers };
  const requestInit = { method, headers: requestHeaders };
  if (body !== undefined) {
    requestHeaders["Content-Type"] = requestHeaders["Content-Type"] || "application/json";
    requestInit.body = requestHeaders["Content-Type"] === "application/json" && typeof body !== "string"
      ? JSON.stringify(body)
      : body;
  }

  const res = await fetch(url.toString(), requestInit);
  if (!res.ok) {
    throw new Error(await parseErrorMessage(res));
  }
  return res.json();
}

export async function fetchSupportedTeams() {
  return apiRequest("/teams");
}

export async function fetchMatchupPrediction(teamA, teamB, neutralSite = true) {
  return apiRequest("/predict-matchup", {
    method: "POST",
    body: { team_a: teamA, team_b: teamB, neutral_site: neutralSite },
  });
}

export async function fetchMatchProbability(teamA, teamB) {
  return apiRequest("/predict", {
    method: "POST",
    body: { team_a: teamA, team_b: teamB },
  });
}

export async function fetchUpsetScore(teamA, teamB, scoreA, scoreB) {
  return apiRequest("/upset", {
    method: "POST",
    body: { team_a: teamA, team_b: teamB, score_a: scoreA, score_b: scoreB },
  });
}

export async function fetchPlayersByNation(nation) {
  return apiRequest(`/players/${encodeURIComponent(nation)}`);
}

export async function fetchTopUpsetPlayers() {
  return apiRequest("/players/top-upsets");
}

export async function fetchGKWallRanking() {
  return apiRequest("/goalkeepers/wall-ranking");
}

export async function fetchPlayers(nation = null, position = null) {
  return apiRequest("/players", { query: { nation, position } });
}

export async function fetchPlayer(name) {
  return apiRequest(`/player/${encodeURIComponent(name)}`);
}

export async function fetchDarkScore(homeTeam, awayTeam, stageName = "group stage") {
  return apiRequest("/dark-score", {
    method: "POST",
    body: { home_team: homeTeam, away_team: awayTeam, stage_name: stageName },
  });
}

export async function fetchDemoPredictions() {
  return apiRequest("/demo-predictions");
}

export async function fetchEloCompare(teamA, teamB) {
  return apiRequest("/elo/compare", {
    method: "POST",
    body: { team_a: teamA, team_b: teamB },
  });
}
