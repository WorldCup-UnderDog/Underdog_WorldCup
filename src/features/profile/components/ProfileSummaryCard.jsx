import { ROUTES } from '../../../routes'

function ProfileSummaryCard({
  loading,
  error,
  displayName,
  username,
  email,
  flagSrc,
  profileComplete,
  missingFields,
}) {
  if (loading) {
    return (
      <article className="dashboard-profile-summary">
        <p className="template-subtitle">Loading your profile...</p>
      </article>
    )
  }

  if (error) {
    return (
      <article className="dashboard-profile-summary">
        <p className="template-alert template-alert-error">{error}</p>
        <p className="dashboard-summary-link-row">
          <a className="template-link" href={ROUTES.PROFILE}>Open Profile</a>
        </p>
      </article>
    )
  }

  return (
    <article className="dashboard-profile-summary">
      <div className="dashboard-profile-summary-head">
        <div className="dashboard-profile-summary-identity">
          {flagSrc ? (
            <img src={flagSrc} alt="" className="dashboard-profile-summary-flag" />
          ) : (
            <span className="dashboard-profile-summary-fallback" aria-hidden="true">🏳️</span>
          )}
          <div>
            <p className="dashboard-profile-summary-name">{displayName}</p>
            <p className="dashboard-profile-summary-handle">
              {username ? `@${username}` : 'No username'}
            </p>
          </div>
        </div>
        <span className={`dashboard-profile-status${profileComplete ? ' complete' : ''}`}>
          {profileComplete ? 'Profile Complete' : 'Profile Incomplete'}
        </span>
      </div>

      <p className="dashboard-profile-summary-email">{email || 'No email available'}</p>
      {!profileComplete && (
        <p className="dashboard-profile-summary-missing">
          Missing: {missingFields.join(', ')}
        </p>
      )}

      <div className="dashboard-summary-link-row">
        <a className="template-button template-button-secondary" href={ROUTES.PROFILE}>
          Edit Profile
        </a>
      </div>
    </article>
  )
}

export default ProfileSummaryCard
