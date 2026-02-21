import { useState, useEffect } from "react";
import { fetchNations, fetchMatchProbability, fetchUpsetScore } from "../lib/api";

export function useMatchData() {
  const [nations, setNations] = useState([]);
  const [teamA, setTeamA] = useState("");
  const [teamB, setTeamB] = useState("");
  const [scoreA, setScoreA] = useState(0);
  const [scoreB, setScoreB] = useState(0);
  const [probResult, setProbResult] = useState(null);
  const [upsetResult, setUpsetResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load nations on mount
  useEffect(() => {
    fetchNations().then(data => {
      setNations(data.nations);
      setTeamA(data.nations[0]);
      setTeamB(data.nations[1]);
    });
  }, []);

  const getProbability = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchMatchProbability(teamA, teamB);
      setProbResult(data);
    } catch (e) {
      setError("Failed to fetch probability");
    } finally {
      setLoading(false);
    }
  };

  const getUpsetScore = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchUpsetScore(teamA, teamB, scoreA, scoreB);
      setUpsetResult(data);
    } catch (e) {
      setError("Failed to fetch upset score");
    } finally {
      setLoading(false);
    }
  };

  return {
    nations, teamA, teamB, scoreA, scoreB,
    setTeamA, setTeamB, setScoreA, setScoreB,
    probResult, upsetResult, loading, error,
    getProbability, getUpsetScore,
  };
}