function RosterControls({
  search,
  onSearchChange,
  filteredCount,
  totalCount,
}) {
  return (
    <div className="roster-controls">
      <input
        type="text"
        className="template-input roster-search"
        value={search}
        onChange={(event) => onSearchChange(event.target.value)}
        placeholder="Search team..."
      />
      <p className="roster-meta">
        Showing {filteredCount} of {totalCount} teams
      </p>
    </div>
  )
}

export default RosterControls
