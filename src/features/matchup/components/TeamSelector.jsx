import { TEAMS, getFlag } from '../constants'

function TeamSelector({ id, label, value, onChange, exclude }) {
  const flag = getFlag(value)

  return (
    <div className="ms-team-selector-wrap">
      <label htmlFor={id} className="ms-team-label">
        {label}
      </label>
      <div className="ms-team-select-shell">
        <span className="ms-team-flag">{flag}</span>
        <select
          id={id}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className="ms-team-select"
        >
          {TEAMS.filter((team) => team !== exclude).map((team) => (
            <option key={team} value={team}>
              {team}
            </option>
          ))}
        </select>
        <span className="ms-team-caret">▼</span>
      </div>
    </div>
  )
}

export default TeamSelector
