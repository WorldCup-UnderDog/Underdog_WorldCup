import { useEffect, useState } from 'react'
import { getSupabaseClient } from '../lib/supabase'
import { ROUTES } from '../routes'

function LoggedInPage() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let mounted = true

    async function loadSession() {
      try {
        const supabase = getSupabaseClient()
        const {
          data: { session },
          error: sessionError,
        } = await supabase.auth.getSession()

        if (sessionError) throw sessionError

        if (!session?.user) {
          window.location.href = ROUTES.LOGIN
          return
        }

        if (mounted) setEmail(session.user.email || '')
      } catch (err) {
        if (mounted) setError(err.message || 'Failed to load session')
      } finally {
        if (mounted) setLoading(false)
      }
    }

    loadSession()

    return () => {
      mounted = false
    }
  }, [])

  async function handleLogout() {
    try {
      const supabase = getSupabaseClient()
      await supabase.auth.signOut()
    } finally {
      window.location.href = ROUTES.HOME
    }
  }

  return (
    <div className="template-page">
      <div className="template-topbar dashboard-topbar">
        <a href={ROUTES.HOME} className="logo">
          UNDER<span>DOG</span>
        </a>
        <button type="button" className="template-button template-button-secondary" onClick={handleLogout}>
          Logout
        </button>
      </div>

      <main className="template-main dashboard-main">
        <section className="template-card dashboard-card">
          <p className="section-label">Temporary App Home</p>
          <h1 className="template-title">You are logged in</h1>
          {loading && <p className="template-subtitle">Checking your session...</p>}
          {!loading && !error && (
            <p className="template-subtitle">Signed in as: {email || 'Unknown user'}</p>
          )}
          {!!error && <p className="template-alert template-alert-error">{error}</p>}

          <div className="dashboard-grid">
            <article className="dashboard-panel">
              <h3>Predictions</h3>
              <p>Select two teams and run a matchup prediction.</p>
              <p style={{ marginTop: '0.7rem' }}>
                <a className="template-link" href={ROUTES.MATCHUP}>
                  Open Matchup Tool
                </a>
              </p>
            </article>
            <article className="dashboard-panel">
              <h3>Team Roster Overview</h3>
              <p>Browse all world cup teams in a static roster list.</p>
              <p style={{ marginTop: '0.7rem' }}>
                <a className="template-link" href={ROUTES.ROSTERS}>
                  Open Team Roster
                </a>
              </p>
            </article>
            <article className="dashboard-panel">
              <h3>Profile</h3>
              <p>Placeholder for account and preferences settings.</p>
            </article>
          </div>
        </section>
      </main>
    </div>
  )
}

export default LoggedInPage
