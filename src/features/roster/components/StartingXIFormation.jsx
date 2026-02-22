import { useMemo } from 'react'
import { buildStartingXIFormation } from '../formation'
import '../starting-xi.css'

function getPlayerStatText(player) {
  if (!player) return ''
  const stats = player.stats || {}
  const segments = []

  if (Number.isFinite(stats.caps)) segments.push(`${stats.caps} caps`)
  if (Number.isFinite(stats.goals)) segments.push(`${stats.goals} goals`)
  if (Number.isFinite(stats.assists)) segments.push(`${stats.assists} assists`)

  if (segments.length > 0) return segments.join(' • ')
  return player.overall != null ? String(player.overall) : ''
}

function renderPlayerCard(player, onPlayerClick, showStats) {
  return (
    <button
      key={`${player.number}-${player.name}`}
      type="button"
      className="xi-player-card"
      onClick={() => onPlayerClick(player)}
      aria-label={`Select ${player.name}`}
    >
      <span className="xi-player-number">#{player.number}</span>
      <span className="xi-player-name">{player.name}</span>
      <span className="xi-player-position">{player.normalized_position || player.position}</span>
      {showStats && (
        <span className="xi-player-stats">{getPlayerStatText(player)}</span>
      )}
    </button>
  )
}

function StartingXIFormation({
  players,
  onPlayerClick = () => {},
  compact = false,
  showStats = true,
  className = '',
}) {
  const { formation, lines } = useMemo(() => buildStartingXIFormation(players), [players])
  const wrapperClassName = `starting-xi${compact ? ' starting-xi-compact' : ''}${className ? ` ${className}` : ''}`

  return (
    <section className={wrapperClassName}>
      <div className="starting-xi-header">
        <p className="section-label">Starting XI Formation</p>
        <p className="starting-xi-formation-value">{formation}</p>
      </div>

      <div className="starting-xi-pitch" role="region" aria-label="Starting lineup field layout">
        <div className="pitch-halfway-line" />
        <div className="pitch-center-circle" />
        <div className="pitch-penalty-box pitch-penalty-box-top" />
        <div className="pitch-penalty-box pitch-penalty-box-bottom" />

        <div className="starting-xi-rows">
          <div className="starting-xi-row starting-xi-row-attack">
            {lines.attack.map((player) => renderPlayerCard(player, onPlayerClick, showStats))}
          </div>
          <div className="starting-xi-row starting-xi-row-midfield">
            {lines.midfield.map((player) => renderPlayerCard(player, onPlayerClick, showStats))}
          </div>
          <div className="starting-xi-row starting-xi-row-defense">
            {lines.defense.map((player) => renderPlayerCard(player, onPlayerClick, showStats))}
          </div>
          <div className="starting-xi-row starting-xi-row-goalkeeper">
            {lines.gk.map((player) => renderPlayerCard(player, onPlayerClick, showStats))}
          </div>
        </div>
      </div>
    </section>
  )
}

export default StartingXIFormation
