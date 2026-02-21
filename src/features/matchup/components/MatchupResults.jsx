import ProbBar from './ProbBar'
import TeamCard from './TeamCard'
import UpsetMeter from './UpsetMeter'

function MatchupResults({ result }) {
  if (!result) return null

  const confidenceColor =
    result.confidence === 'High'
      ? '#4aff9f'
      : result.confidence === 'Medium'
        ? '#f0a500'
        : '#7a8ba0'

  return (
    <div className="results-section">
      <div className="results-header">Prediction Results</div>

      <div className="teams-result-row">
        <TeamCard
          team={result.team_a}
          prob={result.team_a_win_prob}
          isWinner={result.predicted_winner === result.team_a}
          side="left"
        />
        <div className="vs-divider">VS</div>
        <TeamCard
          team={result.team_b}
          prob={result.team_b_win_prob}
          isWinner={result.predicted_winner === result.team_b}
          side="right"
        />
      </div>

      <div className="probs-card">
        <div className="probs-title">Win / Draw / Loss Breakdown</div>
        <div className="probs-bars">
          <ProbBar
            label={result.team_a.split(' ').pop().substring(0, 3).toUpperCase()}
            pct={result.team_a_win_prob}
            color="linear-gradient(90deg, #1a4fff, #2563ff)"
          />
          <ProbBar label="DRW" pct={result.draw_prob} color="rgba(255,255,255,0.25)" />
          <ProbBar
            label={result.team_b.split(' ').pop().substring(0, 3).toUpperCase()}
            pct={result.team_b_win_prob}
            color="linear-gradient(90deg, #e84a4a, #ff6060)"
          />
        </div>
      </div>

      <div className="meta-row">
        <div className="meta-card">
          <UpsetMeter score={result.upset_score} />
        </div>
        <div className="meta-card">
          <div className="meta-card-label">Confidence</div>
          <div className="meta-card-value" style={{ color: confidenceColor }}>
            {result.confidence}
          </div>
          <div className="meta-card-helper">Model certainty level</div>
        </div>
      </div>

      {result.explanation?.length > 0 && (
        <div className="explanation-card">
          <div className="explanation-title">Why This Prediction</div>
          <ul className="explanation-list">
            {result.explanation.map((line) => (
              <li key={line} className="explanation-item">
                {line}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

export default MatchupResults
