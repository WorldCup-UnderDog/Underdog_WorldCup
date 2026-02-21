import { useEffect, useMemo, useState } from 'react'
import { getSupabaseClient } from '../lib/supabase'
import { ROUTES, getTeamRosterRoute } from '../routes'
import RosterControls from '../features/roster/components/RosterControls'
import RosterGrid from '../features/roster/components/RosterGrid'
import RosterHeader from '../features/roster/components/RosterHeader'
import { WORLD_CUP_TEAMS } from '../features/roster/constants'
import { getFlagSrc } from '../features/roster/flags'

function TeamRosterPage() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')

  const filteredTeams = useMemo(() => {
    const query = search.trim().toLowerCase()
    return WORLD_CUP_TEAMS
      .filter((team) => team.toLowerCase().includes(query))
      .sort((a, b) => a.localeCompare(b))
  }, [search])

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
        <div className="topbar-actions">
          <a className="btn-ghost" href={ROUTES.APP}>
            ← Back
          </a>
          <button type="button" className="btn-ghost" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </div>

      <main className="template-main dashboard-main">
        <section className="template-card dashboard-card roster-card">
          <RosterHeader loading={loading} error={error} email={email} />

          {!loading && !error && (
            <>
              <RosterControls
                search={search}
                onSearchChange={setSearch}
                filteredCount={filteredTeams.length}
                totalCount={WORLD_CUP_TEAMS.length}
              />
              <RosterGrid
                teams={filteredTeams}
                getFlagSrc={getFlagSrc}
                getTeamHref={getTeamRosterRoute}
              />
            </>
          )}
        </section>
      </main>
    </div>
  )
}

export default TeamRosterPage
