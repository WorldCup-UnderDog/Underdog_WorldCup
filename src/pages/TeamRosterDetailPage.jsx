import { useEffect, useMemo, useState } from 'react'
import { getSupabaseClient } from '../lib/supabase'
import { fetchProfile } from '../lib/profile'
import { ROUTES } from '../routes'
import { getFlagSrc } from '../features/roster/flags'
import { fetchTeamRoster } from '../features/roster/api'
import StartingXIFormation from '../features/roster/components/StartingXIFormation'
import TeamDiscussion from '../features/roster/components/TeamDiscussion'

function TeamRosterDetailPage({ teamName }) {
  const [email, setEmail] = useState('')
  const [userId, setUserId] = useState(null)
  const [username, setUsername] = useState('')
  const [loadingSession, setLoadingSession] = useState(true)
  const [sessionError, setSessionError] = useState('')

  const [loadingRoster, setLoadingRoster] = useState(true)
  const [rosterError, setRosterError] = useState('')
  const [teamData, setTeamData] = useState(null)
  const [selectedPlayer, setSelectedPlayer] = useState(null)

  const flagSrc = useMemo(() => (teamName ? getFlagSrc(teamName) : null), [teamName])

  useEffect(() => {
    let mounted = true

    async function loadSession() {
      try {
        const supabase = getSupabaseClient()
        const {
          data: { session },
          error,
        } = await supabase.auth.getSession()

        if (error) throw error
        if (!session?.user) {
          window.location.href = ROUTES.LOGIN
          return
        }
        if (mounted) {
          setEmail(session.user.email || '')
          setUserId(session.user.id)
          const profile = await fetchProfile(session.user.id).catch(() => null)
          setUsername(profile?.username || session.user.user_metadata?.full_name || session.user.email || '')
        }
      } catch (err) {
        if (mounted) setSessionError(err.message || 'Failed to load session')
      } finally {
        if (mounted) setLoadingSession(false)
      }
    }

    loadSession()
    return () => {
      mounted = false
    }
  }, [])

  useEffect(() => {
    let mounted = true

    async function loadRoster() {
      setLoadingRoster(true)
      setRosterError('')

      if (!teamName) {
        setRosterError('Missing team in route.')
        setLoadingRoster(false)
        return
      }

      try {
        const payload = await fetchTeamRoster(teamName)
        if (!payload) throw new Error('No static roster found for this team yet.')
        if (mounted) {
          setTeamData(payload)
          setSelectedPlayer(null)
        }
      } catch (err) {
        if (mounted) setRosterError(err.message || 'Failed to load team roster')
      } finally {
        if (mounted) setLoadingRoster(false)
      }
    }

    loadRoster()
    return () => {
      mounted = false
    }
  }, [teamName])

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
          DARK<span>HORSE</span>
        </a>
        <div className="topbar-actions">
          <a className="btn-ghost" href={ROUTES.ROSTERS}>
            ← Back
          </a>
          <button type="button" className="btn-ghost" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </div>

      <main className="template-main dashboard-main">
        <section className="template-card dashboard-card roster-card">
          <p className="section-label">Team Roster Detail</p>
          <h1 className="template-title">{teamName || 'Team'}</h1>
          <p className="template-subtitle">
            Static roster data today. This page is structured for future API and team stats integration.
          </p>

          {loadingSession && <p className="template-subtitle">Checking your session...</p>}
          {!loadingSession && !sessionError && <p className="template-subtitle">Signed in as: {email || 'Unknown user'}</p>}
          {!!sessionError && <p className="template-alert template-alert-error">{sessionError}</p>}

          {!loadingSession && !sessionError && (
            <>
              {loadingRoster && <p className="template-subtitle">Loading team roster...</p>}
              {!!rosterError && <p className="template-alert template-alert-error">{rosterError}</p>}

              {!loadingRoster && !rosterError && teamData && (
                <div className="team-roster-detail">
                  <div className="team-roster-hero">
                    {flagSrc ? (
                      <img className="team-roster-flag" src={flagSrc} alt={`${teamData.team} flag`} />
                    ) : (
                      <span className="team-roster-flag-fallback" aria-hidden="true">🏳️</span>
                    )}
                    <div>
                      <h2 className="team-roster-title">{teamData.team}</h2>
                      <p className="team-roster-subtitle">Confederation: {teamData.stats.confederation}</p>
                    </div>
                  </div>

                  <div className="team-stats-grid">
                    <article className="team-stat-card">
                      <p className="team-stat-label">FIFA Rank</p>
                      <p className="team-stat-value">{teamData.stats.fifa_rank}</p>
                    </article>
                    <article className="team-stat-card">
                      <p className="team-stat-label">World Cup Titles</p>
                      <p className="team-stat-value">{teamData.stats.world_cup_titles}</p>
                    </article>
                    <article className="team-stat-card">
                      <p className="team-stat-label">Recent Form</p>
                      <p className="team-stat-value">{teamData.stats.recent_form}</p>
                    </article>
                  </div>

                  <StartingXIFormation
                    players={teamData.starting_xi || teamData.players}
                    compact={false}
                    showStats={false}
                    onPlayerClick={setSelectedPlayer}
                  />

                  {selectedPlayer && (
                    <div className="selected-player-card">
                      <p className="selected-player-label">Selected Player</p>
                      <p className="selected-player-name">
                        #{selectedPlayer.number} {selectedPlayer.name}
                      </p>
                      <p className="selected-player-meta">
                        Position: {selectedPlayer.position} | Club: {selectedPlayer.club || 'TBD'}
                      </p>
                    </div>
                  )}

                  <div className="team-player-table-wrap">
                    <table className="team-player-table">
                      <thead>
                        <tr>
                          <th>#</th>
                          <th>Player</th>
                          <th>Pos</th>
                          <th>Club</th>
                        </tr>
                      </thead>
                      <tbody>
                        {teamData.players.map((player) => (
                          <tr key={`${teamData.team}-${player.number}-${player.name}`}>
                            <td>{player.number}</td>
                            <td>{player.name}</td>
                            <td>{player.position}</td>
                            <td>{player.club}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <TeamDiscussion teamName={teamName} userId={userId} username={username} />
                </div>
              )}
            </>
          )}
        </section>
      </main>
    </div>
  )
}

export default TeamRosterDetailPage
