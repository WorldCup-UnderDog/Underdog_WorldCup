function RosterTile({ team, flagSrc }) {
  return (
    <article className="roster-tile">
      {flagSrc ? (
        <img className="roster-flag" src={flagSrc} alt={`${team} flag`} loading="lazy" />
      ) : (
        <span className="roster-flag-fallback" aria-hidden="true">🏳️</span>
      )}
      <span className="roster-name">{team}</span>
    </article>
  )
}

export default RosterTile
