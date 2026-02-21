import { useEffect, useMemo, useState } from 'react'
import { getSupabaseClient } from '../lib/supabase'
import { ROUTES } from '../routes'

const FLAG_SVGS = import.meta.glob('../assets/flags/*.svg', { eager: true, import: 'default' })

const WORLD_CUP_TEAMS = [
  'Canada', 'Mexico', 'United States',
  'Australia', 'Iran', 'Japan', 'Jordan', 'South Korea', 'Qatar', 'Saudi Arabia', 'Uzbekistan',
  'Algeria', 'Cape Verde', 'Egypt', 'Ghana', 'Ivory Coast', 'Morocco', 'Senegal', 'South Africa', 'Tunisia',
  'Curaçao', 'Haiti', 'Panama',
  'Argentina', 'Brazil', 'Colombia', 'Ecuador', 'Paraguay', 'Uruguay',
  'New Zealand',
  'Austria', 'Belgium', 'Croatia', 'England', 'France', 'Germany', 'Netherlands',
  'Norway', 'Portugal', 'Scotland', 'Spain', 'Switzerland',
]

const TEAM_TO_FLAG_CODE = {
  'Canada': 'ca',
  'Mexico': 'mx',
  'United States': 'us',
  'Australia': 'au',
  'Iran': 'ir',
  'Japan': 'jp',
  'Jordan': 'jo',
  'South Korea': 'kr',
  'Qatar': 'qa',
  'Saudi Arabia': 'sa',
  'Uzbekistan': 'uz',
  'Algeria': 'dz',
  'Cape Verde': 'cv',
  'Egypt': 'eg',
  'Ghana': 'gh',
  'Ivory Coast': 'ci',
  'Morocco': 'ma',
  'Senegal': 'sn',
  'South Africa': 'za',
  'Tunisia': 'tn',
  'Curaçao': 'cw',
  'Haiti': 'ht',
  'Panama': 'pa',
  'Argentina': 'ar',
  'Brazil': 'br',
  'Colombia': 'co',
  'Ecuador': 'ec',
  'Paraguay': 'py',
  'Uruguay': 'uy',
  'New Zealand': 'nz',
  'Austria': 'at',
  'Belgium': 'be',
  'Croatia': 'hr',
  'England': 'gb-eng',
  'France': 'fr',
  'Germany': 'de',
  'Netherlands': 'nl',
  'Norway': 'no',
  'Portugal': 'pt',
  'Scotland': 'gb-sct',
  'Spain': 'es',
  'Switzerland': 'ch',
}

const getFlagSrc = (team) => {
  const code = TEAM_TO_FLAG_CODE[team]
  if (!code) return null
  return FLAG_SVGS[`../assets/flags/${code}.svg`] || null
}

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
          <a className="template-button template-button-secondary" href={ROUTES.APP}>
            ← Back
          </a>
          <button type="button" className="template-button template-button-secondary" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </div>

      <main className="template-main dashboard-main">
        <section className="template-card dashboard-card roster-card">
          <p className="section-label">Team Roster Overview</p>
          <h1 className="template-title">World Cup Team Pool</h1>
          {loading && <p className="template-subtitle">Checking your session...</p>}
          {!loading && !error && (
            <p className="template-subtitle">Signed in as: {email || 'Unknown user'}</p>
          )}
          {!!error && <p className="template-alert template-alert-error">{error}</p>}

          {!loading && !error && (
            <>
              <div className="roster-controls">
                <input
                  type="text"
                  className="template-input roster-search"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Search team..."
                />
                <p className="roster-meta">
                  Showing {filteredTeams.length} of {WORLD_CUP_TEAMS.length} teams
                </p>
              </div>

              {filteredTeams.length === 0 ? (
                <p className="template-subtitle">No teams found for that search.</p>
              ) : (
                <div className="roster-grid">
                  {filteredTeams.map((team) => {
                    const flagSrc = getFlagSrc(team)
                    return (
                      <article key={team} className="roster-tile">
                        {flagSrc ? (
                          <img className="roster-flag" src={flagSrc} alt={`${team} flag`} loading="lazy" />
                        ) : (
                          <span className="roster-flag-fallback" aria-hidden="true">🏳️</span>
                        )}
                        <span className="roster-name">{team}</span>
                      </article>
                    )
                  })}
                </div>
              )}
            </>
          )}
        </section>
      </main>
    </div>
  )
}

export default TeamRosterPage
