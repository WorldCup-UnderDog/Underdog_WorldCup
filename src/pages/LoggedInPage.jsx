import { useEffect, useMemo, useState } from 'react'
import useMyProfile from '../features/profile/hooks/useMyProfile'
import { getSupabaseClient } from '../lib/supabase'
import { ROUTES } from '../routes'

function ProfileCard({ name, username, email, flagSrc, isComplete, onEdit }) {
  return (
    <article className="dashboard-profile-card dashboard-fade-up">
      <div className="dashboard-profile-card-head">
        <div className="dashboard-profile-card-identity">
          <span className="dashboard-profile-card-flag">
            {flagSrc ? <img className="dashboard-profile-card-flag-image" src={flagSrc} alt="" /> : '🏳️'}
          </span>
          <div>
            <p className="dashboard-profile-card-name">{name}</p>
            <p className="dashboard-profile-card-handle">@{username || 'username'}</p>
          </div>
        </div>
        <span className={`dashboard-profile-pill${isComplete ? ' complete' : ''}`}>
          {isComplete ? 'Profile Complete' : 'Profile Incomplete'}
        </span>
      </div>

      <p className="dashboard-profile-card-email">{email}</p>
      <button
        type="button"
        onClick={onEdit}
        className="dashboard-edit-button"
      >
        Edit Profile
      </button>
    </article>
  )
}

function FeatureCard({ title, description, linkLabel, icon, onClick, isHovered, onHoverChange, animationClass }) {
  return (
    <article
      onMouseEnter={() => onHoverChange(true)}
      onMouseLeave={() => onHoverChange(false)}
      className={`dashboard-feature-card dashboard-fade-up ${animationClass}${isHovered ? ' hovered' : ''}`}
    >
      <div className="dashboard-feature-icon">
        {icon}
      </div>
      <h3 className="dashboard-feature-title">{title}</h3>
      <p className="dashboard-feature-description">{description}</p>

      <button
        type="button"
        onClick={onClick}
        className="dashboard-feature-cta"
      >
        {linkLabel}
        <span className="dashboard-feature-arrow" aria-hidden="true">→</span>
      </button>
    </article>
  )
}

export default function Dashboard() {
  const {
    loading,
    error,
    email,
    displayName,
    username,
    flagSrc,
    profileComplete,
  } = useMyProfile()

  const [hoveredCard, setHoveredCard] = useState('')
  const [clickedAction, setClickedAction] = useState('')

  useEffect(() => {
    const fontLinkId = 'dashboard-display-font'
    const keyframeStyleId = 'dashboard-keyframes'

    let fontLink = document.getElementById(fontLinkId)
    if (!fontLink) {
      fontLink = document.createElement('link')
      fontLink.id = fontLinkId
      fontLink.rel = 'stylesheet'
      fontLink.href = 'https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&display=swap'
      document.head.appendChild(fontLink)
    }

    let keyframeStyle = document.getElementById(keyframeStyleId)
    if (!keyframeStyle) {
      keyframeStyle = document.createElement('style')
      keyframeStyle.id = keyframeStyleId
      keyframeStyle.textContent = `
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `
      document.head.appendChild(keyframeStyle)
    }

    return () => {
      if (fontLink && fontLink.parentNode) fontLink.parentNode.removeChild(fontLink)
      if (keyframeStyle && keyframeStyle.parentNode) keyframeStyle.parentNode.removeChild(keyframeStyle)
    }
  }, [])

  const features = useMemo(
    () => [
      {
        id: 'predictions',
        title: 'Predictions',
        description: 'Select two teams and run a matchup prediction.',
        linkLabel: 'Open Matchup Tool',
        icon: '⚡',
        href: ROUTES.MATCHUP,
      },
      {
        id: 'darkscore',
        title: 'DarkScore — Upset Model',
        description: 'ML-powered upset probability using XGBoost, Elo ratings, and FC player data.',
        linkLabel: 'Open DarkScore FAQ',
        icon: '🎯',
        href: ROUTES.DARKSCORE_FAQ,
      },
      {
        id: 'roster',
        title: 'Team Roster Overview',
        description: 'Browse all world cup teams in a static roster list.',
        linkLabel: 'Open Team Roster',
        icon: '🌍',
        href: ROUTES.ROSTERS,
      },
    ],
    []
  )

  const handleFeatureClick = (feature) => {
    setClickedAction(feature.id)
    window.location.assign(feature.href)
  }

  const handleEditProfile = () => {
    setClickedAction('profile')
    window.location.assign(ROUTES.PROFILE)
  }

  const handleLogout = async () => {
    setClickedAction('logout')
    try {
      const supabase = getSupabaseClient()
      await supabase.auth.signOut()
    } finally {
      window.location.assign(ROUTES.HOME)
    }
  }

  return (
    <div className="template-page dashboard-redesign-page">
      <div aria-hidden="true" className="dashboard-grid-overlay" />

      <header className="template-topbar dashboard-topbar dashboard-redesign-topbar">
        <div className="template-container dashboard-redesign-topbar-inner">
          <a href={ROUTES.HOME} className="logo">
            DARK<span>HORSE</span>
          </a>
          <button
            type="button"
            onClick={handleLogout}
            className="dashboard-logout-button"
          >
            Logout
          </button>
        </div>
      </header>

      <main className="template-main dashboard-main dashboard-redesign-main">
        <section className="template-card dashboard-card dashboard-home-card dashboard-shell">
          <section className="dashboard-fade-up">
            <p className="section-label">App Dashboard</p>
            <h1 className="dashboard-welcome-title">
            Welcome Back
            </h1>
            <p className="dashboard-welcome-subtitle">
              {loading ? 'Checking your session and profile...' : `Signed in as: ${email || 'Unknown user'}`}
            </p>
            {!!error && (
              <p className="template-alert template-alert-error">{error}</p>
            )}
          </section>

          <section className="dashboard-profile-row">
            <ProfileCard
              name={displayName}
              username={username}
              email={email}
              flagSrc={flagSrc}
              isComplete={profileComplete}
              onEdit={handleEditProfile}
            />
          </section>

          <section className="dashboard-feature-grid">
            {features.map((feature, index) => (
              <FeatureCard
                key={feature.id}
                title={feature.title}
                description={feature.description}
                linkLabel={feature.linkLabel}
                icon={feature.icon}
                onClick={() => handleFeatureClick(feature)}
                isHovered={hoveredCard === feature.id}
                onHoverChange={(isOn) => setHoveredCard(isOn ? feature.id : '')}
                animationClass={` dashboard-delay-${Math.min(index + 1, 3)}`}
              />
            ))}
          </section>

          {clickedAction && (
            <p className="dashboard-action-feedback">
              Action triggered: <span>{clickedAction}</span>
            </p>
          )}
        </section>
      </main>
    </div>
  )
}
