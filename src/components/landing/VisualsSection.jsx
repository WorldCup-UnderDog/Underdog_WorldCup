function VisualsSection() {
  return (
    <section id="visuals">
      <div className="section-label">Live Intelligence</div>
      <h2>
        2026 Bracket <span style={{ color: 'var(--accent)' }}>Preview</span>
      </h2>
      <p className="section-sub">
        Example outputs for upset scoring and projected tournament outcomes.
      </p>

      <div className="visuals-grid">
        <div className="bracket-card">
          <h4>Quarter-Final Projections</h4>
          <p className="section-sub" style={{ marginBottom: '1rem', fontSize: '0.9rem' }}>
            Placeholder bracket view for future dynamic predictions.
          </p>
          <div className="chart-bars">
            <div className="chart-row">
              <span className="chart-name">GER vs MAR</span>
              <div className="chart-track">
                <div
                  className="chart-fill animated"
                  style={{
                    width: '78%',
                    background: 'linear-gradient(90deg, var(--accent2), var(--accent))',
                  }}
                >
                  7.8
                </div>
              </div>
            </div>
            <div className="chart-row">
              <span className="chart-name">BRA vs KOR</span>
              <div className="chart-track">
                <div
                  className="chart-fill animated"
                  style={{
                    width: '82%',
                    background: 'linear-gradient(90deg, var(--accent2), var(--accent))',
                  }}
                >
                  8.2
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="chart-card">
          <h4>UPSET SCORE LEADERBOARD</h4>
          <div className="chart-bars">
            <div className="chart-row">
              <span className="chart-name">KOR vs BRA</span>
              <div className="chart-track">
                <div
                  className="chart-fill animated"
                  style={{
                    width: '82%',
                    background: 'linear-gradient(90deg, var(--accent2), var(--accent))',
                  }}
                >
                  8.2
                </div>
              </div>
            </div>
            <div className="chart-row">
              <span className="chart-name">MAR vs GER</span>
              <div className="chart-track">
                <div
                  className="chart-fill animated"
                  style={{
                    width: '78%',
                    background: 'linear-gradient(90deg, var(--accent2), var(--accent))',
                  }}
                >
                  7.8
                </div>
              </div>
            </div>
            <div className="chart-row">
              <span className="chart-name">USA vs PRT</span>
              <div className="chart-track">
                <div
                  className="chart-fill animated"
                  style={{
                    width: '61%',
                    background: 'linear-gradient(90deg, var(--blue), var(--blue-glow))',
                  }}
                >
                  6.1
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default VisualsSection
