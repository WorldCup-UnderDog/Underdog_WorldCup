import { getFlag } from '../constants'

function TeamCard({ team, prob, isWinner, side }) {
  const flag = getFlag(team)

  return (
    <div
      className={`ms-team-card ${isWinner ? 'ms-team-card-winner' : ''}`}
      style={{ textAlign: side === 'left' ? 'left' : 'right' }}
    >
      {isWinner && <div className="ms-winner-badge">PREDICTED WIN</div>}
      <div className="ms-team-emoji">{flag}</div>
      <div className="ms-team-name">{team}</div>
      {prob !== undefined && (
        <div className="ms-team-prob">
          {prob}
          <span>%</span>
        </div>
      )}
    </div>
  )
}

export default TeamCard
