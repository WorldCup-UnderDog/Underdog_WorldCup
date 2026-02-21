function HowItWorksSection() {
  return (
    <div className="how-section" id="how" style={{ maxWidth: '100%', padding: '0 4rem' }}>
      <section style={{ padding: '5rem 0', maxWidth: '1200px', margin: '0 auto' }}>
        <div className="section-label">Process</div>
        <h2>
          How It <span style={{ color: 'var(--accent)' }}>Works</span>
        </h2>
        <p className="section-sub">
          Three stages transform raw team data into upset probability output.
        </p>

        <div className="steps-flow">
          <div className="step-card">
            <div className="step-num">01</div>
            <div className="step-icon-wrap">DATA</div>
            <h3>Collect match and team data</h3>
            <p>Historical results, rankings, and recent form.</p>
          </div>

          <div className="arrow-connector">&gt;</div>

          <div className="step-card">
            <div className="step-num">02</div>
            <div className="step-icon-wrap">MODEL</div>
            <h3>Build prediction model</h3>
            <p>Model produces win/draw/loss probabilities per matchup.</p>
          </div>

          <div className="arrow-connector">&gt;</div>

          <div className="step-card">
            <div className="step-num">03</div>
            <div className="step-icon-wrap">OUTPUT</div>
            <h3>Show upset probabilities</h3>
            <p>Surface likely upsets with quick explanation context.</p>
          </div>
        </div>
      </section>
    </div>
  )
}

export default HowItWorksSection
