import { ROUTES } from '../../../routes'

function MatchupHeader({ onLogout }) {
  return (
    <>
      <nav className="matchup-nav">
        <a href={ROUTES.APP} className="matchup-logo">
          UNDER<span>DOG</span>
        </a>
        <div className="nav-actions">
          <a href={ROUTES.APP} className="btn-ghost">
            Back
          </a>
          <button type="button" className="btn-ghost" onClick={onLogout}>
            Logout
          </button>
        </div>
      </nav>

      <div className="page-header">
        <div className="page-eyebrow">Matchup Predictor</div>
        <h1 className="page-title">
          Team vs <span style={{ color: 'var(--accent)' }}>Team</span>
        </h1>
        <p className="page-sub">
          Select two nations and run an AI-powered probability prediction.
        </p>
      </div>
    </>
  )
}

export default MatchupHeader
