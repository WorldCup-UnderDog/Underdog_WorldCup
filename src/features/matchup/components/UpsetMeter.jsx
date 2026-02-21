function UpsetMeter({ score }) {
  const pct = Math.min((score / 10) * 100, 100)
  const color = score >= 7 ? '#e8c84a' : score >= 4 ? '#f0a500' : '#4a8fff'
  const label = score >= 7 ? 'HIGH' : score >= 4 ? 'MEDIUM' : 'LOW'

  return (
    <div>
      <div className="ms-upset-head">
        <span className="ms-upset-label">UPSET SCORE</span>
        <span className="ms-upset-value-wrap">
          <span className="ms-upset-value" style={{ color }}>{score}</span>
          <span className="ms-upset-denom">/10</span>
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
