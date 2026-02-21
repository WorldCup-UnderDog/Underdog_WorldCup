function UpsetMeter({ score }) {
  const pct = Math.min(Math.max(score, 0), 100)
  const color = score >= 70 ? '#e8c84a' : score >= 40 ? '#f0a500' : '#4a8fff'
  const label = score >= 70 ? 'HIGH' : score >= 40 ? 'MEDIUM' : 'LOW'

  return (
    <div>
      <div className="ms-upset-head">
        <span className="ms-upset-label">UPSET SCORE</span>
        <span className="ms-upset-value-wrap">
          <span className="ms-upset-value" style={{ color }}>{score}</span>
          <span className="ms-upset-denom">/100</span>
        </span>
      </div>
      <div className="ms-upset-track">
        <div
          className="ms-upset-fill"
          style={{
            width: `${pct}%`,
            background: `linear-gradient(90deg, ${color}aa, ${color})`,
          }}
        />
      </div>
      <div className="ms-upset-risk" style={{ color }}>
        {label} UPSET RISK
      </div>
    </div>
  )
}

export default UpsetMeter
