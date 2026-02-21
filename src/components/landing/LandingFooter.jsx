import { ROUTES } from '../../routes'

function LandingFooter() {
  return (
    <footer>
      <div className="footer-left">
        <a href={ROUTES.HOME} className="logo">
          DARK<span>HORSE</span>
        </a>
        <p className="footer-desc">
          World Cup upset intelligence powered by machine learning
        </p>
      </div>

      <div className="footer-right">
        <div className="hackathon-badge">Built for Hackathon 2026</div>
        <p>Elo-based ML modeling · 64 matches · 32 nations</p>
        <p style={{ marginTop: '0.3rem' }}>Prediction model created using Sphinx</p>
        <p
          style={{
            marginTop: '0.3rem',
            fontSize: '0.72rem',
            color: 'rgba(122,139,160,0.5)',
          }}
        >
          Predictions are probabilistic estimates, not guarantees
        </p>
      </div>
    </footer>
  )
}

export default LandingFooter
