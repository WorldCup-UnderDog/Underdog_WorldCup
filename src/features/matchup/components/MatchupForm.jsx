import TeamSelector from './TeamSelector'

function MatchupForm({
  teamA,
  teamB,
  neutralSite,
  submitting,
  onTeamAChange,
  onTeamBChange,
  onSwap,
  onNeutralSiteChange,
  onSubmit,
}) {
  return (
    <form onSubmit={onSubmit}>
      <div className="builder-card">
        <div className="team-selector-row">
          <TeamSelector
            id="team-a"
            label="Home Team / Team A"
            value={teamA}
            onChange={onTeamAChange}
            exclude={teamB}
          />

          <button type="button" className="swap-btn" onClick={onSwap} title="Swap teams">
            ⇄
          </button>

          <TeamSelector
            id="team-b"
            label="Away Team / Team B"
            value={teamB}
            onChange={onTeamBChange}
            exclude={teamA}
          />
        </div>

        <div className="venue-row">
          <span className="venue-label">Venue</span>
          <div className="venue-options">
            <button
              type="button"
              className={`venue-pill${neutralSite ? ' active' : ''}`}
              onClick={() => onNeutralSiteChange(true)}
            >
              Neutral Site
            </button>
            <button
              type="button"
              className={`venue-pill${!neutralSite ? ' active' : ''}`}
              onClick={() => onNeutralSiteChange(false)}
            >
              Team A Home
            </button>
          </div>
        </div>

        <button
          type="submit"
          className={`predict-btn${submitting ? ' loading' : ''}`}
          disabled={submitting}
        >
          {submitting ? 'Running Simulation...' : 'Predict Matchup'}
        </button>
      </div>
    </form>
  )
}

export default MatchupForm
