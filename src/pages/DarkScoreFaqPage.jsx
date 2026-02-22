import { ROUTES } from '../routes'

function FaqBlock({ title, children }) {
  return (
    <section style={{
      background: 'rgba(10,22,40,0.55)',
      border: '1px solid rgba(255,255,255,0.08)',
      borderRadius: '14px',
      padding: '1.2rem 1.3rem',
      marginTop: '1rem',
    }}>
      <h2 style={{
        margin: 0,
        fontFamily: 'var(--font-display)',
        fontSize: '1.6rem',
        letterSpacing: '0.02em',
      }}>
        {title}
      </h2>
      <div style={{ marginTop: '0.6rem', color: 'var(--muted)', lineHeight: 1.6, fontSize: '0.92rem' }}>
        {children}
      </div>
    </section>
  )
}

export default function DarkScoreFaqPage() {
  return (
    <div className="template-page">
      <div className="template-topbar">
        <div className="template-container dashboard-topbar">
          <a href={ROUTES.APP} className="logo">
            DARK<span>HORSE</span>
          </a>
          <div className="topbar-actions">
            <a href={ROUTES.APP} className="btn-ghost">← Dashboard</a>
            <a href={ROUTES.MATCHUP} className="btn-ghost">Open Predictions</a>
          </div>
        </div>
      </div>

      <main className="template-main dashboard-main">
        <section className="template-card dashboard-card" style={{ width: 'min(980px, 100%)' }}>
          <p className="section-label">FAQ</p>
          <h1 className="template-title" style={{ marginBottom: '0.6rem' }}>DarkScore Guide</h1>
          <p className="template-subtitle" style={{ marginBottom: 0 }}>
            Simple explanation of DarkScore, Dark Knight, and Upset Score.
          </p>

          <FaqBlock title="What Is DarkScore?">
            DarkScore is a 0-100 model score for upset pressure. It is calibrated around 
             model features like Elo, recent form, stage context, and FC player stats.
          </FaqBlock>

          <FaqBlock title="What Is Dark Knight?">
            Dark Knight highlights the player contributors tied to the current upset context:
            low-range games surface favorite control players, mean-range games surface one underdog x-factor,
            and high-range games surface the top two underdog drivers.
          </FaqBlock>

          <FaqBlock title="What Is Upset Score?">
            Upset Score is a quicker heuristic from matchup probabilities. It is useful as a fast volatility signal,
            while DarkScore is the richer ML upset indicator.
          </FaqBlock>

          <FaqBlock title="DarkScore Vs Upset Score">
            Use DarkScore when you want model-driven upset analysis. Use Upset Score for a fast read of match uncertainty.
            If they disagree, treat DarkScore as the upset-specific signal and Upset Score as general volatility context.
          </FaqBlock>

          <FaqBlock title="How is Elo Calculated?">
            We obtained each team’s Elo rating by starting with a baseline rating and then updating it match by match using the standard Elo formula. 
            For every game in our dataset, we calculated the expected win probability based on the rating difference between the two teams. After the match result was known, we adjusted each team’s rating depending on whether they performed better or worse than expected.
            If a team won when they were expected to lose, their rating increased more; if they lost when favored, their rating decreased. We repeated this process sequentially across historical matches, which allowed ratings to evolve over time and reflect long-term team performance. 
            The final ratings used in production are the most recent values from this historical update process.
          </FaqBlock>

        </section>
      </main>
    </div>
  )
}
