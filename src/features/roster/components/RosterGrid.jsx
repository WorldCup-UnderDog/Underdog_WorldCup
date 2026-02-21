import RosterTile from './RosterTile'

function RosterGrid({ teams, getFlagSrc }) {
  if (teams.length === 0) {
    return <p className="template-subtitle">No teams found for that search.</p>
  }

  return (
    <div className="roster-grid">
      {teams.map((team) => (
        <RosterTile key={team} team={team} flagSrc={getFlagSrc(team)} />
      ))}
    </div>
  )
}

export default RosterGrid
