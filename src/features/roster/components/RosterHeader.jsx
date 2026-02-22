function RosterHeader({ loading, error, email }) {
  return (
    <>
      <p className="section-label">Team Roster Overview</p>
      <h1 className="template-title">World Cup Team Pool</h1>
      {loading && <p className="template-subtitle">Checking your session...</p>}
      {!loading && !error && <p className="template-subtitle">Signed in as: {email || 'Unknown user'}</p>}
      {!!error && <p className="template-alert template-alert-error">{error}</p>}
    </>
  )
}

export default RosterHeader
