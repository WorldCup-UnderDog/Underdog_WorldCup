function ProfileChip({ href, displayName, username, flagSrc }) {
  return (
    <a href={href} className="dashboard-profile-chip" aria-label="Open profile">
      {flagSrc ? (
        <img src={flagSrc} alt="" className="dashboard-profile-chip-flag" />
      ) : (
        <span className="dashboard-profile-chip-fallback" aria-hidden="true">🏳️</span>
      )}
      <span className="dashboard-profile-chip-text">
        <span className="dashboard-profile-chip-name">{displayName}</span>
        <span className="dashboard-profile-chip-handle">{username ? `@${username}` : 'Profile'}</span>
      </span>
    </a>
  )
}

export default ProfileChip
