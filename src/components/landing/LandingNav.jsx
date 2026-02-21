import { ROUTES } from '../../routes'

function LandingNav() {
  return (
    <nav>
      <a href={ROUTES.HOME} className="logo">
        UNDER<span>DOG</span>
      </a>
      <ul>
        <li>
          <a href="#features">Features</a>
        </li>
        <li>
          <a href="#how">Methodology</a>
        </li>
        <li>
          <a href="#visuals">Predictions</a>
        </li>
        <li>
          <a href={ROUTES.LOGIN}>Login</a>
        </li>
        <li>
          <a href={ROUTES.SIGNUP} className="nav-cta">
            Sign Up
          </a>
        </li>
      </ul>
    </nav>
  )
}

export default LandingNav
