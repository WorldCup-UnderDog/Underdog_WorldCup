function StatsBar() {
  return (
    <div className="stats-bar" style={{ maxWidth: '100%' }}>
      <div className="stat-item">
        <span className="stat-num">64</span>
        <div className="stat-label">Matches Modeled</div>
      </div>
      <div className="stat-item">
        <span className="stat-num">32</span>
        <div className="stat-label">Teams Analyzed</div>
      </div>
      <div className="stat-item">
        <span className="stat-num">89%</span>
        <div className="stat-label">Prediction Accuracy</div>
      </div>
      <div className="stat-item">
        <span className="stat-num">12</span>
        <div className="stat-label">Upsets Flagged</div>
      </div>
    </div>
  )
}

export default StatsBar
