import '../player-profile-card.css'

// ── Stat bar ───────────────────────────────────────────────────────────────
function StatBar({ label, value, max = 100 }) {
  const v = value ?? 0
  const pct = Math.min(Math.max(v / max, 0), 1) * 100
  return (
    <div className="ppc-stat-row">
      <span className="ppc-stat-label">{label}</span>
      <div className="ppc-stat-bar-wrap">
        <div className="ppc-stat-bar-fill" style={{ width: `${pct}%` }} />
      </div>
      <span className="ppc-stat-value">{Math.round(v)}</span>
    </div>
  )
}

// ── Hexagon radar chart ────────────────────────────────────────────────────
const CX = 130, CY = 130, R = 75, LABEL_R = 104

function RadarChart({ axes }) {
  const n = axes.length
  const startAngle = -Math.PI / 2

  const polarToXY = (i, radius, pct = 1) => {
    const angle = startAngle + (i * 2 * Math.PI) / n
    return [CX + radius * pct * Math.cos(angle), CY + radius * pct * Math.sin(angle)]
  }

  const gridPolygons = [0.2, 0.4, 0.6, 0.8, 1.0].map((pct) => {
    const pts = Array.from({ length: n }, (_, i) => polarToXY(i, R, pct).join(',')).join(' ')
    return <polygon key={pct} points={pts} className="ppc-radar-grid" />
  })

  const axisLines = Array.from({ length: n }, (_, i) => {
    const [x2, y2] = polarToXY(i, R)
    return <line key={i} x1={CX} y1={CY} x2={x2} y2={y2} className="ppc-radar-axis" />
  })

  const dataPoints = axes
    .map((ax, i) => polarToXY(i, R, Math.min(Math.max(ax.value / 100, 0), 1)).join(','))
    .join(' ')

  const labelEls = axes.map((ax, i) => {
    const [x, y] = polarToXY(i, LABEL_R)
    return (
      <text key={i} x={x} y={y} className="ppc-radar-label" textAnchor="middle" dominantBaseline="middle">
        {ax.label}
      </text>
    )
  })

  return (
    <svg viewBox="0 0 260 260" className="ppc-radar-svg">
      {gridPolygons}
      {axisLines}
      <polygon points={dataPoints} className="ppc-radar-data" />
      {labelEls}
    </svg>
  )
}

// ── Main component ─────────────────────────────────────────────────────────
export default function PlayerProfileCard({ player, onClose }) {
  const isGK = (player.position || '').toUpperCase() === 'GK'

  const overall   = Number(player.overall ?? 0)
  const potential = Number(player.potential ?? 0)
  const gap       = Math.round(potential - overall)

  // Derived stats (mirroring player_profile.py)
  const gkAbility  = Math.min(Math.round((player.total_goalkeeping ?? 0) / 5), 100)
  const dist       = Math.round(((player.short_passing ?? 0) + (player.long_passing ?? 0)) / 2)
  const pace       = Math.round(((player.acceleration ?? 0) + (player.sprint_speed ?? 0)) / 2)
  const defending  = Math.min(Math.round((player.total_defending ?? 0) / 5), 100)
  const physical   = Math.min(Math.round((player.total_power ?? 0) / 5), 100)

  const radarAxes = isGK
    ? [
        { label: 'GK Ability',   value: gkAbility },
        { label: 'Reactions',    value: player.reactions ?? 0 },
        { label: 'Distribution', value: dist },
        { label: 'Sweeping',     value: player.sprint_speed ?? 0 },
        { label: 'Aerial',       value: player.heading_accuracy ?? 0 },
        { label: 'Positioning',  value: player.acceleration ?? 0 },
      ]
    : [
        { label: 'Pace',      value: pace },
        { label: 'Shooting',  value: player.finishing ?? 0 },
        { label: 'Passing',   value: dist },
        { label: 'Dribbling', value: player.dribbling ?? 0 },
        { label: 'Defending', value: defending },
        { label: 'Physical',  value: physical },
      ]

  return (
    <div className="ppc-overlay" role="dialog" aria-modal="true" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="ppc-card">
        <button className="ppc-close" onClick={onClose} type="button" aria-label="Close profile">✕</button>

        {/* ── Header ── */}
        <div className="ppc-header">
          <h2 className="ppc-name">
            {player.name}
            {isGK && <span className="ppc-gk-badge">GK</span>}
          </h2>
          <p className="ppc-meta">
            {player.nation ? `${player.nation} · ` : ''}{player.position}
          </p>
        </div>

        {/* ── Ratings ── */}
        <div className="ppc-ratings-grid">
          {[
            { label: 'Overall',   val: Math.round(overall) },
            { label: 'Potential', val: Math.round(potential) },
            { label: 'Gap',       val: gap > 0 ? `+${gap}` : gap, positive: gap > 0 },
            { label: 'Age',       val: player.age ?? '—' },
            { label: 'Value',     val: player.value || '—', small: true },
          ].map(({ label, val, positive, small }) => (
            <div key={label} className="ppc-rating-item">
              <span className="ppc-rating-label">{label}</span>
              <span className={[
                'ppc-rating-value',
                positive ? 'ppc-rating-positive' : '',
                small    ? 'ppc-rating-small'    : '',
              ].filter(Boolean).join(' ')}>
                {val}
              </span>
            </div>
          ))}
        </div>

        {/* ── Playstyles ── */}
        {player.playstyles?.length > 0 && (
          <div className="ppc-section">
            <p className="ppc-section-title">Playstyles</p>
            <div className="ppc-playstyles">
              {player.playstyles.map((ps) => (
                <span key={ps} className="ppc-playstyle-chip">{ps}</span>
              ))}
            </div>
          </div>
        )}

        {/* ── Key attributes + category totals (two columns) ── */}
        <div className="ppc-columns">
          <div className="ppc-section">
            <p className="ppc-section-title">{isGK ? 'Key GK Attributes' : 'Key Attributes'}</p>
            {isGK ? (
              <>
                <StatBar label="GK Ability"  value={gkAbility} />
                <StatBar label="Reactions"   value={player.reactions ?? 0} />
                <StatBar label="Handling"    value={player.ball_control ?? 0} />
                <StatBar label="Kicking"     value={player.long_passing ?? 0} />
                <StatBar label="Aerial Reach" value={player.heading_accuracy ?? 0} />
              </>
            ) : (
              <>
                <StatBar label="Acceleration"  value={player.acceleration ?? 0} />
                <StatBar label="Sprint Speed"  value={player.sprint_speed ?? 0} />
                <StatBar label="Dribbling"     value={player.dribbling ?? 0} />
                <StatBar label="Finishing"     value={player.finishing ?? 0} />
                <StatBar label="Short Passing" value={player.short_passing ?? 0} />
              </>
            )}
          </div>

          <div className="ppc-section">
            <p className="ppc-section-title">Category Totals</p>
            {isGK ? (
              <>
                <StatBar label="Goalkeeping" value={player.total_goalkeeping ?? 0} max={500} />
                <StatBar label="Movement"    value={player.total_movement ?? 0}    max={500} />
                <StatBar label="Power"       value={player.total_power ?? 0}       max={500} />
                <StatBar label="Mentality"   value={player.total_mentality ?? 0}   max={500} />
              </>
            ) : (
              <>
                <StatBar label="Attacking" value={player.total_attacking ?? 0} max={500} />
                <StatBar label="Skill"     value={player.total_skill ?? 0}     max={500} />
                <StatBar label="Movement"  value={player.total_movement ?? 0}  max={500} />
                <StatBar label="Power"     value={player.total_power ?? 0}     max={500} />
                <StatBar label="Mentality" value={player.total_mentality ?? 0} max={500} />
                <StatBar label="Defending" value={player.total_defending ?? 0} max={500} />
              </>
            )}
          </div>
        </div>

        {/* ── Hexagon radar ── */}
        <div className="ppc-section">
          <p className="ppc-section-title">{isGK ? 'Save Profile Radar' : 'Attribute Radar'}</p>
          <RadarChart axes={radarAxes} />
        </div>
      </div>
    </div>
  )
}