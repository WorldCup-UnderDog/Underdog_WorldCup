import { ROUTES } from '../../routes'

function HeroSection() {
  return (
    <section
      className="hero"
      style={{ maxWidth: '100%', paddingTop: '8rem', paddingBottom: '4rem' }}
    >
      <div className="orb orb-blue" />
      <div className="orb orb-gold" />

      <div className="hero-content">
        <div className="hero-badge">
          WORLD CUP 2026 - MODEL CREATED USING SPHINX
        </div>
        <h1>
          Predicting the Next World Cup <span className="accent">Upset.</span>
        </h1>
        <p className="hero-sub">
          AI-powered match predictions that quantify underdog probability using
          Elo modeling, form metrics, and machine learning.
        </p>
        <div className="hero-actions">
          <a href="#visuals" className="btn-primary">
            Explore Upset Predictions
          </a>
          <a href="#how" className="btn-secondary">
            View Methodology
          </a>
          <a href={ROUTES.LOGIN} className="btn-secondary">
            Login
          </a>
          <a href={ROUTES.SIGNUP} className="btn-primary">
            Sign Up
          </a>
        </div>
      </div>

      <div className="hero-visual">
        <div className="match-card">
          <div className="match-header">
            <span className="match-label">GROUP STAGE - MATCH 14</span>
            <span className="upset-badge">HIGH UPSET RISK</span>
          </div>

          <div className="teams">
            <div className="team">
              <div className="team-flag">DE</div>
              <div className="team-name">Germany</div>
              <div className="team-rank">Elo #4</div>
            </div>
            <div className="vs">VS</div>
            <div className="team">
              <div className="team-flag">MA</div>
              <div className="team-name">Morocco</div>
              <div className="team-rank">Elo #14</div>
            </div>
          </div>

          <div className="prob-bars">
            <div className="prob-row">
              <span className="prob-label">GER</span>
              <div className="prob-bar-track">
                <div className="prob-bar-fill fill-win animated" style={{ width: '42%' }} />
              </div>
              <span className="prob-val">42%</span>
            </div>
            <div className="prob-row">
              <span className="prob-label">DRW</span>
              <div className="prob-bar-track">
                <div className="prob-bar-fill fill-draw animated" style={{ width: '27%' }} />
              </div>
              <span className="prob-val">27%</span>
            </div>
            <div className="prob-row">
              <span className="prob-label">MAR</span>
              <div className="prob-bar-track">
                <div className="prob-bar-fill fill-loss animated" style={{ width: '31%' }} />
              </div>
              <span className="prob-val">31%</span>
            </div>
          </div>

          <div className="upset-score-row">
            <div>
              <div className="upset-label">UPSET SCORE</div>
              <div className="upset-value">7.8</div>
            </div>
            <div>
              <div
                className="upset-value"
                style={{ fontSize: '1rem', color: 'var(--muted)', textAlign: 'right' }}
              >
                Model: XGBoost
                <br />+ Elo v2.1
              </div>
              <div className="upset-desc">Morocco overperforming</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}

export default HeroSection
