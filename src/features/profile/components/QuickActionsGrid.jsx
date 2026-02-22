function QuickActionsGrid({ actions }) {
  return (
    <div className="dashboard-actions-grid">
      {actions.map((action) => (
        <article key={action.title} className="dashboard-panel">
          <h3>{action.title}</h3>
          <p>{action.description}</p>
          <p className="dashboard-panel-link-row">
            <a className="template-link" href={action.href}>
              {action.cta}
            </a>
          </p>
        </article>
      ))}
    </div>
  )
}

export default QuickActionsGrid
