function FeaturesSection() {
  return (
    <section id="features">
      <div className="section-label">Core Capabilities</div>
      <h2>
        Built for the <span style={{ color: 'var(--accent)' }}>Beautiful Game</span>
      </h2>
      <p className="section-sub">
        Three analytical modules that surface where dark horses can outperform
        expectations.
      </p>

      <div className="features-grid">
        <div className="feature-card">
          <div className="feature-icon">WDL</div>
          <h3>Match Probability Engine</h3>
          <p>Win, draw, and loss probabilities for each fixture.</p>
          <div className="step-tags">
            <span className="tag">Win %</span>
            <span className="tag">Draw %</span>
            <span className="tag">Loss %</span>
          </div>
          <div className="feature-tag">Probability Output</div>
        </div>

        <div className="feature-card">
          <div className="feature-icon">US</div>
          <h3>Upset Score</h3>
          <p>Composite score that quantifies how likely an upset is.</p>
          <div className="step-tags">
            <span className="tag">Elo Delta</span>
            <span className="tag">Form</span>
            <span className="tag">Matchup</span>
          </div>
          <div className="feature-tag">Upset Quantification</div>
        </div>

        <div className="feature-card">
          <div className="feature-icon">AI</div>
          <h3>Explainable Factors</h3>
          <p>Short explanations for why a potential upset is flagged.</p>
          <div className="step-tags">
            <span className="tag">Reasoning</span>
            <span className="tag">Confidence</span>
            <span className="tag">Context</span>
          </div>
          <div className="feature-tag">Data-Driven Context</div>
        </div>
      </div>
    </section>
  )
}

export default FeaturesSection
