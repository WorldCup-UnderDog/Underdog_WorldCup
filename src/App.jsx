import { useEffect, useRef } from 'react'
import './App.css'

const landingMarkup = `
<nav>
  <a href="#" class="logo">UNDER<span>DOG</span></a>
  <ul>
    <li><a href="#features">Features</a></li>
    <li><a href="#how">Methodology</a></li>
    <li><a href="#visuals">Predictions</a></li>
    <li><a href="#" class="nav-cta">Explore Now</a></li>
  </ul>
</nav>

<section class="hero" style="max-width: 100%; padding-top: 8rem; padding-bottom: 4rem;">
  <div class="orb orb-blue"></div>
  <div class="orb orb-gold"></div>

  <div class="hero-content">
    <div class="hero-badge">⚽ WORLD CUP 2026 &nbsp;·&nbsp; MODEL CREATED USING SPHINX</div>
    <h1>Predicting the Next World Cup <span class="accent">Upset.</span></h1>
    <p class="hero-sub">AI-powered match predictions that quantify underdog probability using Elo modeling, form metrics, and machine learning.</p>
    <div class="hero-actions">
      <a href="#visuals" class="btn-primary">Explore Upset Predictions →</a>
      <a href="#how" class="btn-secondary">View Methodology</a>
    </div>
  </div>

  <div class="hero-visual">
    <div class="match-card">
      <div class="match-header">
        <span class="match-label">GROUP STAGE · MATCH 14</span>
        <span class="upset-badge">⚠ HIGH UPSET RISK</span>
      </div>

      <div class="teams">
        <div class="team">
          <div class="team-flag">🇩🇪</div>
          <div class="team-name">Germany</div>
          <div class="team-rank">Elo #4</div>
        </div>
        <div class="vs">VS</div>
        <div class="team">
          <div class="team-flag">🇲🇦</div>
          <div class="team-name">Morocco</div>
          <div class="team-rank">Elo #14</div>
        </div>
      </div>

      <div class="prob-bars">
        <div class="prob-row">
          <span class="prob-label">GER</span>
          <div class="prob-bar-track">
            <div class="prob-bar-fill fill-win animated" style="width: 42%"></div>
          </div>
          <span class="prob-val">42%</span>
        </div>
        <div class="prob-row">
          <span class="prob-label">DRW</span>
          <div class="prob-bar-track">
            <div class="prob-bar-fill fill-draw animated" style="width: 27%"></div>
          </div>
          <span class="prob-val">27%</span>
        </div>
        <div class="prob-row">
          <span class="prob-label">MAR</span>
          <div class="prob-bar-track">
            <div class="prob-bar-fill fill-loss animated" style="width: 31%"></div>
          </div>
          <span class="prob-val">31%</span>
        </div>
      </div>

      <div class="upset-score-row">
        <div>
          <div class="upset-label">UPSET SCORE</div>
          <div class="upset-value">7.8</div>
        </div>
        <div>
          <div class="upset-value" style="font-size: 1rem; color: var(--muted); text-align: right;">Model: XGBoost<br>+ Elo v2.1</div>
          <div class="upset-desc">↑ Morocco overperforming</div>
        </div>
      </div>
    </div>
  </div>
</section>

<div class="stats-bar" style="max-width:100%;">
  <div class="stat-item">
    <span class="stat-num">64</span>
    <div class="stat-label">Matches Modeled</div>
  </div>
  <div class="stat-item">
    <span class="stat-num">32</span>
    <div class="stat-label">Teams Analyzed</div>
  </div>
  <div class="stat-item">
    <span class="stat-num">89%</span>
    <div class="stat-label">Prediction Accuracy</div>
  </div>
  <div class="stat-item">
    <span class="stat-num">12</span>
    <div class="stat-label">Upsets Flagged</div>
  </div>
</div>

<section id="features">
  <div class="section-label">Core Capabilities</div>
  <h2>Built for the <span style="color:var(--accent)">Beautiful Game</span></h2>
  <p class="section-sub">Three powerful analytical modules working in concert to surface the matches where history gets rewritten.</p>

  <div class="features-grid">
    <div class="feature-card">
      <div class="feature-icon">⚡</div>
      <h3>Match Probability Engine</h3>
      <p>Computes granular win, draw, and loss probabilities for every matchup using a ensemble of gradient boosted models trained on 20+ years of international fixtures.</p>
      <div class="step-tags">
        <span class="tag">Win %</span>
        <span class="tag">Draw %</span>
        <span class="tag">Loss %</span>
        <span class="tag">xGoals</span>
      </div>
      <div class="feature-tag">→ Probability Output</div>
    </div>

    <div class="feature-card">
      <div class="feature-icon">🎯</div>
      <h3>Upset Score</h3>
      <p>A proprietary 0–10 composite index that quantifies underdog win likelihood beyond raw odds. Accounts for Elo gap, recent form volatility, and tactical matchup factors.</p>
      <div class="step-tags">
        <span class="tag">Elo Delta</span>
        <span class="tag">Form Index</span>
        <span class="tag">Home Factor</span>
      </div>
      <div class="feature-tag">→ Upset Quantification</div>
    </div>

    <div class="feature-card">
      <div class="feature-icon">🔍</div>
      <h3>Explainable AI</h3>
      <p>Every prediction comes with SHAP-powered feature importance breakdowns. Understand exactly which factors drive each forecast — no black boxes, full transparency.</p>
      <div class="step-tags">
        <span class="tag">SHAP Values</span>
        <span class="tag">Feature Impact</span>
        <span class="tag">Confidence</span>
      </div>
      <div class="feature-tag">→ Data-Driven Reasoning</div>
    </div>
  </div>
</section>

<div class="how-section" id="how" style="max-width:100%; padding: 0 4rem;">
  <section style="padding: 5rem 0; max-width: 1200px; margin: 0 auto;">
    <div class="section-label">Process</div>
    <h2>How It <span style="color:var(--accent)">Works</span></h2>
    <p class="section-sub">Three stages transform raw team data into actionable upset intelligence.</p>

    <div class="steps-flow">
      <div class="step-card">
        <div class="step-num">01</div>
        <div class="step-icon-wrap">📊</div>
        <h3>Team Strength Modeling</h3>
        <p>Ingests historical match results, FIFA rankings, and recent form to compute dynamic Elo ratings for each national team. Weighted recency ensures current form shapes predictions.</p>
        <div class="step-tags">
          <span class="tag">Elo Rating</span>
          <span class="tag">Form Decay</span>
          <span class="tag">H2H History</span>
          <span class="tag">Tournament Weight</span>
        </div>
      </div>

      <div class="arrow-connector">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="rgba(26,79,255,0.5)" stroke-width="2">
          <path d="M5 12h14M12 5l7 7-7 7"/>
        </svg>
      </div>

      <div class="step-card">
        <div class="step-num">02</div>
        <div class="step-icon-wrap">⚙️</div>
        <h3>Match Simulation</h3>
        <p>XGBoost and logistic regression models simulate each fixture 10,000 times using bootstrapped team strength distributions, producing probability densities rather than point estimates.</p>
        <div class="step-tags">
          <span class="tag">XGBoost</span>
          <span class="tag">Monte Carlo</span>
          <span class="tag">Scikit-learn</span>
          <span class="tag">10k Sims</span>
        </div>
      </div>

      <div class="arrow-connector">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="rgba(26,79,255,0.5)" stroke-width="2">
          <path d="M5 12h14M12 5l7 7-7 7"/>
        </svg>
      </div>

      <div class="step-card">
        <div class="step-num">03</div>
        <div class="step-icon-wrap">🏆</div>
        <h3>Upset Probability Output</h3>
        <p>Simulation results are aggregated into win/draw/loss probabilities and a composite Upset Score. SHAP values identify the key drivers flagged as risk factors for surprises.</p>
        <div class="step-tags">
          <span class="tag">Upset Score</span>
          <span class="tag">SHAP</span>
          <span class="tag">Confidence CI</span>
          <span class="tag">FastAPI</span>
        </div>
      </div>
    </div>
  </section>
</div>

<section id="visuals">
  <div class="section-label">Live Intelligence</div>
  <h2>2026 Bracket <span style="color:var(--accent)">Preview</span></h2>
  <p class="section-sub">Early bracket projections with embedded upset risk scores for every stage of the tournament.</p>

  <div class="visuals-grid">
    <div class="bracket-card">
      <h4>⚽ Quarter-Final Projections</h4>
      <div class="bracket" style="overflow-x: auto; gap: 1.5rem; align-items: flex-start;">

        <div class="bracket-round">
          <div class="round-label">QF</div>
          <div class="match-slot">
            <div class="slot-team winner"><span class="flag-sm">🇫🇷</span> France <span class="upset-indicator" style="opacity:0"> </span></div>
            <div class="slot-team"><span class="flag-sm">🇲🇦</span> Morocco <span class="upset-indicator">⚠ 7.8</span></div>
          </div>
          <div class="match-slot">
            <div class="slot-team winner"><span class="flag-sm">🇦🇷</span> Argentina</div>
            <div class="slot-team"><span class="flag-sm">🇳🇱</span> Netherlands</div>
          </div>
          <div class="match-slot">
            <div class="slot-team"><span class="flag-sm">🇧🇷</span> Brazil <span class="upset-indicator">⚠ 6.1</span></div>
            <div class="slot-team winner"><span class="flag-sm">🇰🇷</span> South Korea</div>
          </div>
          <div class="match-slot">
            <div class="slot-team winner"><span class="flag-sm">🇩🇪</span> Germany</div>
            <div class="slot-team"><span class="flag-sm">🏴</span> England</div>
          </div>
        </div>

        <div style="display:flex;align-items:center;padding-top:2rem;">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="rgba(26,79,255,0.4)" stroke-width="1.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </div>

        <div class="bracket-round">
          <div class="round-label">SF</div>
          <div class="match-slot" style="margin-top: 2.5rem;">
            <div class="slot-team winner"><span class="flag-sm">🇫🇷</span> France</div>
            <div class="slot-team"><span class="flag-sm">🇦🇷</span> Argentina</div>
          </div>
          <div class="match-slot" style="margin-top: 2rem;">
            <div class="slot-team"><span class="flag-sm">🇰🇷</span> South Korea <span class="upset-indicator">⚠ 8.2</span></div>
            <div class="slot-team winner"><span class="flag-sm">🇩🇪</span> Germany</div>
          </div>
        </div>

        <div style="display:flex;align-items:center;padding-top:2rem;">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="rgba(26,79,255,0.4)" stroke-width="1.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
        </div>

        <div class="bracket-round">
          <div class="round-label">FINAL</div>
          <div class="match-slot" style="margin-top: 5rem; min-width: 120px;">
            <div class="slot-team winner"><span class="flag-sm">🇫🇷</span> France</div>
            <div class="slot-team"><span class="flag-sm">🇩🇪</span> Germany</div>
          </div>
        </div>
      </div>

      <div style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--glass-border); display: flex; gap: 1rem; font-size: 0.7rem; color: var(--muted); font-family: 'JetBrains Mono', monospace;">
        <span>🟦 Projected winner</span>
        <span style="color: var(--accent);">⚠ Upset risk flagged</span>
      </div>
    </div>

    <div class="chart-card">
      <h4>UPSET SCORE LEADERBOARD</h4>
      <div class="chart-bars">
        <div class="chart-row">
          <span class="chart-name">KOR vs BRA</span>
          <div class="chart-track">
            <div class="chart-fill animated" style="width: 82%; background: linear-gradient(90deg, var(--accent2), var(--accent));">8.2</div>
          </div>
        </div>
        <div class="chart-row">
          <span class="chart-name">MAR vs GER</span>
          <div class="chart-track">
            <div class="chart-fill animated" style="width: 78%; background: linear-gradient(90deg, var(--accent2), var(--accent));">7.8</div>
          </div>
        </div>
        <div class="chart-row">
          <span class="chart-name">IRN vs ESP</span>
          <div class="chart-track">
            <div class="chart-fill animated" style="width: 72%; background: linear-gradient(90deg, #ff8a00, #ffb300);">7.2</div>
          </div>
        </div>
        <div class="chart-row">
          <span class="chart-name">GHA vs FRA</span>
          <div class="chart-track">
            <div class="chart-fill animated" style="width: 65%; background: linear-gradient(90deg, var(--blue), var(--blue-glow));">6.5</div>
          </div>
        </div>
        <div class="chart-row">
          <span class="chart-name">USA vs PRT</span>
          <div class="chart-track">
            <div class="chart-fill animated" style="width: 61%; background: linear-gradient(90deg, var(--blue), var(--blue-glow));">6.1</div>
          </div>
        </div>
        <div class="chart-row">
          <span class="chart-name">MEX vs ARG</span>
          <div class="chart-track">
            <div class="chart-fill animated" style="width: 55%; background: rgba(255,255,255,0.2);">5.5</div>
          </div>
        </div>
        <div class="chart-row">
          <span class="chart-name">SEN vs ENG</span>
          <div class="chart-track">
            <div class="chart-fill animated" style="width: 49%; background: rgba(255,255,255,0.15);">4.9</div>
          </div>
        </div>
      </div>

      <div style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--glass-border);">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div style="font-size: 0.72rem; color: var(--muted); font-family: 'JetBrains Mono', monospace;">SCORE RANGE</div>
          <div style="display: flex; gap: 1rem; font-size: 0.7rem; font-family: 'JetBrains Mono', monospace;">
            <span style="color: rgba(255,255,255,0.3);">● LOW 0–4</span>
            <span style="color: var(--blue-glow);">● MED 4–7</span>
            <span style="color: var(--accent);">● HIGH 7+</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<footer>
  <div class="footer-left">
    <a href="#" class="logo">UNDER<span>DOG</span></a>
    <p class="footer-desc">World Cup upset intelligence powered by machine learning</p>
  </div>

  <div class="footer-right">
    <div class="hackathon-badge">🏆 Built for Hackathon 2026</div>
    <p>Elo-based ML modeling · 64 matches · 32 nations</p>
    <p style="margin-top: 0.3rem;">Prediction model created using Sphinx</p>
    <p style="margin-top: 0.3rem; font-size: 0.72rem; color: rgba(122,139,160,0.5);">Predictions are probabilistic estimates, not guarantees</p>
  </div>
</footer>
`

function App() {
  const pageRef = useRef(null)

  useEffect(() => {
    if (!pageRef.current) return undefined

    const root = pageRef.current
    const fills = root.querySelectorAll('.prob-bar-fill')
    const widths = ['42%', '27%', '31%']

    fills.forEach((el, i) => {
      el.style.width = '0'
      setTimeout(() => {
        el.style.width = widths[i]
      }, 900 + i * 100)
    })

    const chartObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.querySelectorAll('.chart-fill').forEach((el, i) => {
              const target = el.style.width
              el.style.width = '0'
              setTimeout(() => {
                el.style.width = target
              }, 100 + i * 80)
            })
            chartObserver.unobserve(entry.target)
          }
        })
      },
      { threshold: 0.3 }
    )

    root.querySelectorAll('.chart-card').forEach((el) => chartObserver.observe(el))

    const revealObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.style.opacity = '1'
            entry.target.style.transform = 'translateY(0)'
          }
        })
      },
      { threshold: 0.1 }
    )

    root
      .querySelectorAll('.feature-card, .step-card, .bracket-card, .chart-card')
      .forEach((el) => {
        el.style.opacity = '0'
        el.style.transform = 'translateY(20px)'
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease'
        revealObserver.observe(el)
      })

    return () => {
      chartObserver.disconnect()
      revealObserver.disconnect()
    }
  }, [])

  return <div ref={pageRef} dangerouslySetInnerHTML={{ __html: landingMarkup }} />
}

export default App
