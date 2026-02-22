import { useState, useEffect } from "react";
import { fetchPlayers } from "../lib/api";

export function usePlayerData(nation, position) {
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!nation) return;
    setLoading(true);
    fetchPlayers(nation, position)
      .then(setPlayers)
      .finally(() => setLoading(false));
  }, [nation, position]);

  return { players, loading };
}