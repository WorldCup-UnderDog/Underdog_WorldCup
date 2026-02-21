function ProbBar({ label, pct, color }) {
  return (
    <div className="ms-prob-row">
      <span className="ms-prob-label">{label}</span>
      <div className="ms-prob-track">
        <div className="ms-prob-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="ms-prob-val">{pct}%</span>
    </div>
  )
}

export default ProbBar
