import { useEffect, useMemo, useState } from 'react'
import { getSupabaseClient } from '../lib/supabase'
import { ROUTES } from '../routes'
import MatchupHeader from '../features/matchup/components/MatchupHeader'
import MatchupForm from '../features/matchup/components/MatchupForm'
import MatchupResults from '../features/matchup/components/MatchupResults'
import '../features/matchup/matchup.css'

function MatchupPage() {
  const [loadingSession, setLoadingSession] = useState(true)
  const [sessionError, setSessionError] = useState('')

  const [teamA, setTeamA] = useState('Germany')
  const [teamB, setTeamB] = useState('Morocco')
  const [neutralSite, setNeutralSite] = useState(true)

  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [hasRun, setHasRun] = useState(false)

  const apiBaseUrl = useMemo(
    () => (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, ''),
    []
  )

  useEffect(() => {
    let mounted = true

    async function checkSession() {
      try {
        const supabase = getSupabaseClient()
        const {
          data: { session },
          error: authError,
        } = await supabase.auth.getSession()

        if (authError) throw authError
        if (!session?.user) {
          window.location.href = ROUTES.LOGIN
          return
        }
      } catch (err) {
        if (mounted) setSessionError(err.message || 'Failed to validate session')
      } finally {
        if (mounted) setLoadingSession(false)
      }
    }

    checkSession()

    return () => {
      mounted = false
    }
  }, [])

  async function handlePredict(event) {
    event.preventDefault()
    setError('')

    if (teamA === teamB) {
      setError('Please choose two different teams.')
      return
    }

    setSubmitting(true)

    try {
      const response = await fetch(`${apiBaseUrl}/predict-matchup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          team_a: teamA,
          team_b: teamB,
          neutral_site: neutralSite,
        }),
      })

      if (!response.ok) {
        throw new Error(`Prediction request failed (${response.status})`)
      }

      const data = await response.json()
      setResult(data)
      setHasRun(true)
    } catch (err) {
      setError(err.message || 'Failed to fetch prediction')
    } finally {
      setSubmitting(false)
    }
  }

  function handleSwap() {
    setTeamA(teamB)
    setTeamB(teamA)
    setResult(null)
    setHasRun(false)
  }

  function handleTeamAChange(team) {
    setTeamA(team)
    setResult(null)
    setHasRun(false)
  }

  function handleTeamBChange(team) {
    setTeamB(team)
    setResult(null)
    setHasRun(false)
  }

  async function handleLogout() {
    try {
      const supabase = getSupabaseClient()
      await supabase.auth.signOut()
    } finally {
      window.location.href = ROUTES.HOME
    }
  }

  return (
    <div className="matchup-page">
      <MatchupHeader onLogout={handleLogout} />

      <main className="matchup-main">
        {loadingSession && <div className="ms-status">Checking session...</div>}
        {!!sessionError && <div className="error-alert">{sessionError}</div>}

        {!loadingSession && !sessionError && (
          <MatchupForm
            teamA={teamA}
            teamB={teamB}
            neutralSite={neutralSite}
            submitting={submitting}
            onTeamAChange={handleTeamAChange}
            onTeamBChange={handleTeamBChange}
            onSwap={handleSwap}
            onNeutralSiteChange={setNeutralSite}
            onSubmit={handlePredict}
          />
        )}

        {!!error && <div className="error-alert">{error}</div>}

        {result && hasRun && <MatchupResults result={result} />}
      </main>
    </div>
  )
}

export default MatchupPage
