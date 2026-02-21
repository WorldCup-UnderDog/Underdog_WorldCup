function RosterTile({ team, flagSrc, href }) {
  const body = (
    <>
      {flagSrc ? (
        <img className="roster-flag" src={flagSrc} alt={`${team} flag`} loading="lazy" />
      ) : (
        <span className="roster-flag-fallback" aria-hidden="true">🏳️</span>
      )}
      <span className="roster-name">{team}</span>
    </>
  )

  if (href) {
    return (
      <a className="roster-tile roster-tile-link" href={href}>
        {body}
      </a>
    )
  }

  return <article className="roster-tile">{body}</article>
}

export default RosterTile
