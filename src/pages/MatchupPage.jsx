import { useEffect, useMemo, useState } from 'react'
import { getSupabaseClient } from '../lib/supabase'
import { ROUTES } from '../routes'
import { fetchDarkScore, fetchDemoPredictions } from '../lib/api'

const DEFAULT_TEAMS = [
  'Canada', 'Mexico', 'United States',
  'Australia', 'Iran', 'Japan', 'Jordan', 'South Korea', 'Qatar', 'Saudi Arabia', 'Uzbekistan',
  'Algeria', 'Cape Verde', 'Egypt', 'Ghana', 'Ivory Coast', 'Morocco', 'Senegal', 'South Africa', 'Tunisia',
  'Curaçao', 'Haiti', 'Panama',
  'Argentina', 'Brazil', 'Colombia', 'Ecuador', 'Paraguay', 'Uruguay',
  'New Zealand',
  'Austria', 'Belgium', 'Croatia', 'England', 'France', 'Germany', 'Netherlands',
  'Norway', 'Portugal', 'Scotland', 'Spain', 'Switzerland',
]

const FLAG_MAP = {
  'Canada': '🇨🇦', 'Mexico': '🇲🇽', 'United States': '🇺🇸',
  'Australia': '🇦🇺', 'Iran': '🇮🇷', 'Japan': '🇯🇵', 'Jordan': '🇯🇴',
  'South Korea': '🇰🇷', 'Qatar': '🇶🇦', 'Saudi Arabia': '🇸🇦', 'Uzbekistan': '🇺🇿',
  'Algeria': '🇩🇿', 'Cape Verde': '🇨🇻', 'Egypt': '🇪🇬', 'Ghana': '🇬🇭',
  'Ivory Coast': '🇨🇮', 'Morocco': '🇲🇦', 'Senegal': '🇸🇳', 'South Africa': '🇿🇦', 'Tunisia': '🇹🇳',
  'Curaçao': '🇨🇼', 'Haiti': '🇭🇹', 'Panama': '🇵🇦',
  'Argentina': '🇦🇷', 'Brazil': '🇧🇷', 'Colombia': '🇨🇴', 'Ecuador': '🇪🇨',
  'Paraguay': '🇵🇾', 'Uruguay': '🇺🇾', 'New Zealand': '🇳🇿',
  'Austria': '🇦🇹', 'Belgium': '🇧🇪', 'Croatia': '🇭🇷', 'England': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
  'France': '🇫🇷', 'Germany': '🇩🇪', 'Netherlands': '🇳🇱', 'Norway': '🇳🇴',
  'Portugal': '🇵🇹', 'Scotland': '🏴󠁧󠁢󠁳󠁣󠁴󠁿', 'Spain': '🇪🇸', 'Switzerland': '🇨🇭',
}

const getFlag = (team) => FLAG_MAP[team] || '🏳️'

function getDarkScoreTier(score) {
  if (score >= 60) {
    return { label: 'UPSET ALERT', color: 'var(--accent)' }
  }
  if (score >= 40) {
    return { label: 'WATCHLIST', color: '#f0a500' }
  }
  return { label: 'LOW UPSET RISK', color: '#4a8fff' }
}

function UpsetMeter({ score }) {
  const pct = Math.min(Math.max(score, 0), 100)
  const color = score >= 70 ? '#e8c84a' : score >= 40 ? '#f0a500' : '#4a8fff'
  const label = score >= 70 ? 'HIGH' : score >= 40 ? 'MEDIUM' : 'LOW'
  return (
    <div style={{ width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.5rem' }}>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', color: 'var(--muted)', letterSpacing: '0.1em' }}>
          UPSET SCORE
        </span>
        <span style={{ display: 'flex', alignItems: 'baseline', gap: '0.4rem' }}>
          <span style={{ fontFamily: 'var(--font-display)', fontSize: '2.4rem', lineHeight: 1, color }}>{score}</span>
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.65rem', color: 'var(--muted)' }}>/100</span>
        </span>
      </div>
      <div style={{ height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '100px', overflow: 'hidden' }}>
        <div style={{
          height: '100%', width: `${pct}%`, background: `linear-gradient(90deg, ${color}aa, ${color})`,
          borderRadius: '100px', transition: 'width 1.2s cubic-bezier(0.16,1,0.3,1)',
        }} />
      </div>
      <div style={{ marginTop: '0.4rem', fontFamily: 'var(--font-mono)', fontSize: '0.6rem', color, letterSpacing: '0.12em' }}>
        {label} UPSET RISK
      </div>
    </div>
  )
}

function ProbBar({ label, pct, color }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
      <span style={{ width: '34px', fontFamily: 'var(--font-mono)', fontSize: '0.65rem', color: 'var(--muted)', flexShrink: 0 }}>{label}</span>
      <div style={{ flex: 1, height: '8px', background: 'rgba(255,255,255,0.06)', borderRadius: '100px', overflow: 'hidden' }}>
        <div style={{
          height: '100%', width: `${pct}%`, background: color,
          borderRadius: '100px', transition: 'width 1.2s cubic-bezier(0.16,1,0.3,1)',
        }} />
      </div>
      <span style={{ width: '36px', textAlign: 'right', fontFamily: 'var(--font-mono)', fontSize: '0.75rem', fontWeight: 600, color: 'var(--text)' }}>
        {pct}%
      </span>
    </div>
  )
}

function TeamCard({ team, prob, isWinner, side }) {
  const flag = getFlag(team)
  return (
    <div style={{
      flex: 1,
      background: isWinner ? 'rgba(26,79,255,0.08)' : 'rgba(255,255,255,0.02)',
      border: `1px solid ${isWinner ? 'rgba(26,79,255,0.3)' : 'rgba(255,255,255,0.07)'}`,
      borderRadius: '14px',
      padding: '1.5rem',
      textAlign: side === 'left' ? 'left' : 'right',
      position: 'relative',
      overflow: 'hidden',
      transition: 'border-color 0.3s',
    }}>
      {isWinner && (
        <div style={{
          position: 'absolute', top: '0.6rem', [side === 'left' ? 'right' : 'left']: '0.6rem',
          fontFamily: 'var(--font-mono)', fontSize: '0.55rem', color: '#4aff9f',
          background: 'rgba(74,255,159,0.1)', border: '1px solid rgba(74,255,159,0.25)',
          padding: '0.2rem 0.45rem', borderRadius: '4px', letterSpacing: '0.08em',
        }}>PREDICTED WIN</div>
      )}
      <div style={{ fontSize: '2.8rem', marginBottom: '0.5rem', lineHeight: 1 }}>{flag}</div>
      <div style={{ fontFamily: 'var(--font-display)', fontSize: '1.5rem', letterSpacing: '0.03em', marginBottom: '0.2rem' }}>{team}</div>
      {prob !== undefined && (
        <div style={{ fontFamily: 'var(--font-display)', fontSize: '2.8rem', lineHeight: 1, color: isWinner ? '#4a8fff' : 'var(--muted)' }}>
          {prob}<span style={{ fontSize: '1rem', color: 'var(--muted)' }}>%</span>
        </div>
      )}
    </div>
  )
}

function TeamSelector({ id, label, value, onChange, exclude, teams, disabled = false }) {
  const flag = getFlag(value)
  return (
    <div style={{ flex: 1 }}>
      <label htmlFor={id} style={{
        display: 'block', fontFamily: 'var(--font-mono)', fontSize: '0.65rem',
        letterSpacing: '0.12em', color: 'var(--muted)', marginBottom: '0.5rem', textTransform: 'uppercase',
      }}>{label}</label>
      <div style={{ position: 'relative' }}>
        <span style={{
          position: 'absolute', left: '0.9rem', top: '50%', transform: 'translateY(-50%)',
          fontSize: '1.3rem', pointerEvents: 'none', zIndex: 1,
        }}>{flag}</span>
        <select
          id={id}
          value={value}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value)}
          style={{
            width: '100%',
            background: 'rgba(10,22,40,0.8)',
            border: '1px solid rgba(255,255,255,0.09)',
            borderRadius: '10px',
            color: 'var(--text)',
            fontFamily: 'var(--font-body)',
            fontSize: '0.9rem',
            fontWeight: 500,
            padding: '0.8rem 1rem 0.8rem 3rem',
            appearance: 'none',
            cursor: disabled ? 'not-allowed' : 'pointer',
            opacity: disabled ? 0.7 : 1,
            outline: 'none',
            transition: 'border-color 0.2s',
          }}
          onFocus={e => e.target.style.borderColor = 'rgba(26,79,255,0.5)'}
          onBlur={e => e.target.style.borderColor = 'rgba(255,255,255,0.09)'}
        >
          {teams.filter(t => t !== exclude).map((team) => (
            <option key={team} value={team} style={{ background: '#0a1628' }}>{team}</option>
          ))}
        </select>
        <span style={{
          position: 'absolute', right: '0.9rem', top: '50%', transform: 'translateY(-50%)',
          color: 'var(--muted)', pointerEvents: 'none', fontSize: '0.7rem',
        }}>▼</span>
      </div>
    </div>
  )
}

function MatchupPage() {
  const [loadingSession, setLoadingSession] = useState(true)
  const [sessionError, setSessionError] = useState('')
  const [loadingTeams, setLoadingTeams] = useState(true)
  const [teamsError, setTeamsError] = useState('')
  const [teamOptions, setTeamOptions] = useState(DEFAULT_TEAMS)

  const [teamA, setTeamA] = useState('Germany')
  const [teamB, setTeamB] = useState('Morocco')
  const [neutralSite, setNeutralSite] = useState(true)

  const [stageName, setStageName] = useState('group stage')

  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [hasRun, setHasRun] = useState(false)

  const [darkScoreResult, setDarkScoreResult] = useState(null)
  const [darkScoreError, setDarkScoreError] = useState('')

  const [demoPredictions, setDemoPredictions] = useState([])
  const [demoOpen, setDemoOpen] = useState(false)

  const apiBaseUrl = useMemo(
    () => (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, ''),
    []
  )

  useEffect(() => {
    let mounted = true
    async function checkSession() {
      try {
        const supabase = getSupabaseClient()
        const { data: { session }, error: authError } = await supabase.auth.getSession()
        if (authError) throw authError
        if (!session?.user) { window.location.href = ROUTES.LOGIN; return }
      } catch (err) {
        if (mounted) setSessionError(err.message || 'Failed to validate session')
      } finally {
        if (mounted) setLoadingSession(false)
      }
    }
    checkSession()
    return () => { mounted = false }
  }, [])

  useEffect(() => {
    let mounted = true
    async function loadSupportedTeams() {
      setLoadingTeams(true)
      setTeamsError('')
      try {
        const response = await fetch(`${apiBaseUrl}/teams`)
        if (!response.ok) {
          const payload = await response.json().catch(() => ({}))
          throw new Error(payload.detail || `Failed to load teams (${response.status})`)
        }
        const payload = await response.json()
        const teams = Array.isArray(payload?.teams) ? payload.teams.filter(Boolean) : []
        if (teams.length < 2) throw new Error('Model team list is empty.')

        if (mounted) {
          setTeamOptions(teams)
          setTeamA((prevA) => {
            const nextA = teams.includes(prevA) ? prevA : teams[0]
            setTeamB((prevB) => {
              if (prevB !== nextA && teams.includes(prevB)) return prevB
              return teams.find((team) => team !== nextA) || nextA
            })
            return nextA
          })
        }
      } catch (err) {
        if (mounted) {
          setTeamOptions(DEFAULT_TEAMS)
          const baseMessage = err.message || 'Failed to sync teams from API.'
          setTeamsError(`${baseMessage} (API: ${apiBaseUrl})`)
        }
      } finally {
        if (mounted) setLoadingTeams(false)
      }
    }

    loadSupportedTeams()
    return () => { mounted = false }
  }, [apiBaseUrl])

  useEffect(() => {
    let mounted = true
    fetchDemoPredictions()
      .then(data => { if (mounted) setDemoPredictions(data?.predictions || []) })
      .catch(() => {})
    return () => { mounted = false }
  }, [])

  async function handlePredict(event) {
    event.preventDefault()
    setError('')
    setDarkScoreError('')
    setDarkScoreResult(null)
    if (loadingTeams) { setError('Still loading model-supported teams. Please wait.'); return }
    if (teamOptions.length < 2) { setError('No supported teams are available right now.'); return }
    if (teamA === teamB) { setError('Please choose two different teams.'); return }
    setSubmitting(true)
    try {
      const [matchupRes, darkRes] = await Promise.allSettled([
        fetch(`${apiBaseUrl}/predict-matchup`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ team_a: teamA, team_b: teamB, neutral_site: neutralSite }),
        }).then(async r => {
          if (!r.ok) {
            const payload = await r.json().catch(() => ({}))
            throw new Error(payload.detail || `Prediction request failed (${r.status})`)
          }
          return r.json()
        }),
        fetchDarkScore(teamA, teamB, stageName),
      ])
      if (matchupRes.status === 'fulfilled') {
        setResult(matchupRes.value)
        setHasRun(true)
      } else {
        setError(matchupRes.reason?.message || 'Failed to fetch prediction')
      }
      if (darkRes.status === 'fulfilled') {
        setDarkScoreResult(darkRes.value)
      } else {
        setDarkScoreError(darkRes.reason?.message || 'DarkScore unavailable')
      }
    } finally {
      setSubmitting(false)
    }
  }

  function handleSwap() { setTeamA(teamB); setTeamB(teamA); setResult(null); setHasRun(false); setDarkScoreResult(null) }

  async function handleLogout() {
    try { const supabase = getSupabaseClient(); await supabase.auth.signOut() }
    finally { window.location.href = ROUTES.HOME }
  }

  const confidenceLevel = (result?.confidence || '').toLowerCase()
  const confidenceColor = confidenceLevel === 'high' ? '#4aff9f' : confidenceLevel === 'medium' ? '#f0a500' : '#7a8ba0'

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600&family=JetBrains+Mono:wght@400;600&display=swap');

        :root {
          --bg: #040810;
          --bg2: #070d1a;
          --navy: #0a1628;
          --accent: #e8c84a;
          --accent2: #f0a500;
          --blue: #1a4fff;
          --blue-glow: #2563ff;
          --text: #e8edf5;
          --muted: #7a8ba0;
          --glass: rgba(255,255,255,0.04);
          --glass-border: rgba(255,255,255,0.08);
          --font-display: 'Bebas Neue', sans-serif;
          --font-body: 'DM Sans', sans-serif;
          --font-mono: 'JetBrains Mono', monospace;
        }

        .matchup-page {
          min-height: 100vh;
          background: var(--bg);
          color: var(--text);
          font-family: var(--font-body);
        }

        .matchup-nav {
          position: sticky; top: 0; z-index: 50;
          display: flex; align-items: center; justify-content: space-between;
          padding: 1rem 2rem;
          background: rgba(4,8,16,0.85);
          backdrop-filter: blur(20px);
          border-bottom: 1px solid var(--glass-border);
        }

        .matchup-logo {
          font-family: var(--font-display);
          font-size: 1.4rem; letter-spacing: 0.15em;
          color: var(--accent); text-decoration: none;
        }
        .matchup-logo span { color: var(--text); }

        .nav-actions { display: flex; gap: 0.5rem; }

        .matchup-main {
          max-width: 900px; margin: 0 auto;
          padding: 3rem 2rem 5rem;
        }

        .page-header { margin-bottom: 2.5rem; }
        .page-eyebrow {
          display: inline-flex; align-items: center; gap: 0.5rem;
          font-family: var(--font-mono); font-size: 0.65rem;
          color: var(--accent); letter-spacing: 0.12em;
          margin-bottom: 0.6rem;
        }
        .page-eyebrow::before { content: ''; width: 20px; height: 1px; background: var(--accent); }

        .page-title {
          font-family: var(--font-display);
          font-size: clamp(2.8rem, 6vw, 4.5rem);
          line-height: 0.95; letter-spacing: 0.02em;
          margin: 0 0 0.6rem;
        }

        .page-sub { color: var(--muted); font-size: 0.9rem; margin: 0; }

        /* ── MATCHUP BUILDER ── */
        .builder-card {
          background: rgba(10,22,40,0.6);
          border: 1px solid var(--glass-border);
          border-radius: 20px;
          padding: 2rem;
          margin-bottom: 1.5rem;
          position: relative;
          overflow: hidden;
        }

        .builder-card::before {
          content: '';
          position: absolute; inset: 0;
          background: radial-gradient(ellipse at top left, rgba(26,79,255,0.05), transparent 60%);
          pointer-events: none;
        }

        .team-selector-row {
          display: flex;
          align-items: flex-end;
          gap: 1rem;
          margin-bottom: 1.5rem;
        }

        .swap-btn {
          width: 40px; height: 40px; flex-shrink: 0;
          background: rgba(255,255,255,0.05);
          border: 1px solid var(--glass-border);
          border-radius: 10px;
          color: var(--muted);
          font-size: 1rem;
          cursor: pointer;
          display: flex; align-items: center; justify-content: center;
          transition: all 0.2s;
          margin-bottom: 2px;
        }
        .swap-btn:hover { background: rgba(255,255,255,0.1); color: var(--text); transform: rotate(180deg); }

        .venue-row {
          display: flex;
          align-items: center;
          gap: 1.5rem;
          padding: 1rem 1.2rem;
          background: rgba(255,255,255,0.02);
          border: 1px solid var(--glass-border);
          border-radius: 10px;
          margin-bottom: 1.5rem;
        }

        .venue-label {
          font-family: var(--font-mono); font-size: 0.65rem;
          color: var(--muted); letter-spacing: 0.1em; text-transform: uppercase;
          flex-shrink: 0;
        }

        .venue-options { display: flex; gap: 0.6rem; }

        .venue-pill {
          padding: 0.3rem 0.8rem;
          border-radius: 100px;
          border: 1px solid var(--glass-border);
          background: transparent;
          color: var(--muted);
          font-family: var(--font-body); font-size: 0.8rem; font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
        }
        .venue-pill.active {
          background: rgba(26,79,255,0.2);
          border-color: rgba(26,79,255,0.5);
          color: var(--text);
        }
        .venue-pill:hover:not(.active) { border-color: rgba(255,255,255,0.15); color: var(--text); }

        .predict-btn {
          width: 100%;
          padding: 1rem;
          background: var(--accent);
          color: #040810;
          border: none;
          border-radius: 12px;
          font-family: var(--font-body); font-size: 0.95rem; font-weight: 700;
          letter-spacing: 0.04em;
          cursor: pointer;
          transition: transform 0.2s, box-shadow 0.2s, opacity 0.2s;
          box-shadow: 0 0 30px rgba(232,200,74,0.15);
        }
        .predict-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 0 40px rgba(232,200,74,0.3);
        }
        .predict-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

        .predict-btn.loading {
          background: linear-gradient(90deg, #c9a830, var(--accent), #c9a830);
          background-size: 200%;
          animation: shimmer 1.5s infinite;
        }
        @keyframes shimmer {
          0% { background-position: -200% 0; }
          100% { background-position: 200% 0; }
        }

        .error-alert {
          display: flex; align-items: center; gap: 0.6rem;
          padding: 0.75rem 1rem;
          background: rgba(255,64,64,0.08);
          border: 1px solid rgba(255,64,64,0.2);
          border-radius: 10px;
          color: #ff8080;
          font-size: 0.85rem;
          margin-top: 0.8rem;
        }

        /* ── RESULTS ── */
        .results-section {
          animation: fadeUp 0.5s ease forwards;
        }
        @keyframes fadeUp {
          from { opacity: 0; transform: translateY(16px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .results-header {
          display: flex; align-items: center; gap: 0.6rem;
          margin-bottom: 1rem;
          font-family: var(--font-mono); font-size: 0.65rem;
          color: var(--muted); letter-spacing: 0.1em; text-transform: uppercase;
        }
        .results-header::before { content: ''; flex: 1; height: 1px; background: var(--glass-border); }
        .results-header::after { content: ''; flex: 1; height: 1px; background: var(--glass-border); }

        .teams-result-row {
          display: flex; gap: 1rem; margin-bottom: 1rem;
          align-items: stretch;
        }

        .vs-divider {
          display: flex; align-items: center; justify-content: center;
          width: 44px; flex-shrink: 0;
          font-family: var(--font-display); font-size: 1.2rem;
          color: var(--muted); letter-spacing: 0.08em;
        }

        .probs-card {
          background: rgba(10,22,40,0.6);
          border: 1px solid var(--glass-border);
          border-radius: 14px;
          padding: 1.5rem;
          margin-bottom: 1rem;
        }

        .probs-title {
          font-family: var(--font-mono); font-size: 0.62rem;
          color: var(--muted); letter-spacing: 0.1em; text-transform: uppercase;
          margin-bottom: 1rem;
        }

        .probs-bars { display: flex; flex-direction: column; gap: 0.7rem; }

        .meta-row {
          display: grid; grid-template-columns: 1fr 1fr;
          gap: 1rem; margin-bottom: 1rem;
        }

        .meta-card {
          background: rgba(10,22,40,0.6);
          border: 1px solid var(--glass-border);
          border-radius: 14px;
          padding: 1.2rem 1.5rem;
          display: flex; flex-direction: column; gap: 0.3rem;
        }

        .meta-card-label {
          font-family: var(--font-mono); font-size: 0.62rem;
          color: var(--muted); letter-spacing: 0.1em; text-transform: uppercase;
        }

        .meta-card-value {
          font-family: var(--font-display); font-size: 1.6rem; line-height: 1;
        }

        .explanation-card {
          background: rgba(10,22,40,0.4);
          border: 1px solid var(--glass-border);
          border-radius: 14px;
          padding: 1.5rem;
        }

        .explanation-title {
          font-family: var(--font-mono); font-size: 0.62rem;
          color: var(--muted); letter-spacing: 0.1em; text-transform: uppercase;
          margin-bottom: 1rem;
          display: flex; align-items: center; gap: 0.5rem;
        }
        .explanation-title::after { content: ''; flex: 1; height: 1px; background: var(--glass-border); }

        .explanation-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 0.5rem; }

        .explanation-item {
          display: flex; align-items: flex-start; gap: 0.6rem;
          font-size: 0.86rem; color: var(--muted); line-height: 1.5;
        }
        .explanation-item::before {
          content: '→';
          color: var(--accent); font-family: var(--font-mono); font-size: 0.75rem;
          flex-shrink: 0; margin-top: 0.1rem;
        }

        /* ── DARKSCORE CARD ── */
        .darkscore-card {
          background: rgba(10,22,40,0.7);
          border: 1px solid rgba(232,200,74,0.18);
          border-radius: 20px;
          padding: 1.8rem 2rem;
          margin-top: 1rem;
          position: relative;
          overflow: hidden;
        }
        .darkscore-card::before {
          content: '';
          position: absolute; inset: 0;
          background: radial-gradient(ellipse at top right, rgba(232,200,74,0.06), transparent 60%);
          pointer-events: none;
        }
        .darkscore-header {
          display: flex; align-items: center; justify-content: space-between;
          margin-bottom: 1.4rem;
        }
        .darkscore-label {
          font-family: var(--font-mono); font-size: 0.65rem;
          color: var(--accent); letter-spacing: 0.14em; text-transform: uppercase;
        }
        .darkscore-alert-badge {
          font-family: var(--font-mono); font-size: 0.6rem; letter-spacing: 0.1em;
          padding: 0.25rem 0.6rem; border-radius: 100px;
          background: rgba(232,200,74,0.15); border: 1px solid rgba(232,200,74,0.35);
          color: var(--accent);
        }
        .darkscore-tier-badge {
          font-family: var(--font-mono); font-size: 0.58rem; letter-spacing: 0.1em;
          padding: 0.2rem 0.55rem; border-radius: 100px;
          border: 1px solid currentColor;
          text-transform: uppercase;
        }
        .darkscore-main {
          display: flex; align-items: flex-end; gap: 2rem;
          margin-bottom: 1.4rem; flex-wrap: wrap;
        }
        .darkscore-number-wrap { display: flex; align-items: baseline; gap: 0.3rem; }
        .darkscore-number { font-family: var(--font-display); line-height: 1; }
        .darkscore-of { font-family: var(--font-mono); font-size: 0.7rem; color: var(--muted); }
        .darkscore-teams { display: flex; flex-direction: column; gap: 0.3rem; }
        .darkscore-team-row { font-size: 0.82rem; color: var(--muted); }
        .darkscore-team-row strong { color: var(--text); }
        .elo-bar-section { margin-bottom: 1.2rem; }
        .elo-bar-labels {
          display: flex; justify-content: space-between;
          font-family: var(--font-mono); font-size: 0.6rem; color: var(--muted);
          margin-bottom: 0.35rem;
        }
        .elo-bar-track {
          height: 6px; background: rgba(255,255,255,0.06);
          border-radius: 100px; overflow: hidden; display: flex;
        }
        .elo-bar-home { height: '100%'; background: linear-gradient(90deg, #1a4fff, #2563ff); border-radius: '100px 0 0 100px'; }
        .elo-bar-away { height: '100%'; background: linear-gradient(90deg, #e84a4a, #ff6060); border-radius: '0 100px 100px 0'; }
        .darkscore-insight {
          margin-bottom: 1rem;
          background: rgba(255,255,255,0.02);
          border: 1px solid var(--glass-border);
          border-radius: 12px;
          padding: 0.9rem 1rem;
        }
        .darkscore-insight-title {
          font-family: var(--font-mono); font-size: 0.58rem;
          color: var(--muted); letter-spacing: 0.1em; text-transform: uppercase;
          margin-bottom: 0.45rem;
        }
        .darkscore-insight-summary {
          font-size: 0.84rem;
          color: var(--text);
          line-height: 1.5;
        }
        .dark-knight-card {
          margin-bottom: 0.6rem;
          border-radius: 12px;
          border: 1px solid rgba(232,200,74,0.3);
          background: rgba(232,200,74,0.06);
          padding: 0.9rem 1rem;
        }
        .dark-knight-label {
          font-family: var(--font-mono); font-size: 0.58rem;
          color: var(--accent); letter-spacing: 0.12em; text-transform: uppercase;
          margin-bottom: 0.45rem;
        }
        .dark-knight-player {
          font-family: var(--font-display);
          font-size: 1.4rem;
          letter-spacing: 0.02em;
          color: var(--text);
          line-height: 1;
        }
        .dark-knight-meta {
          margin-top: 0.25rem;
          font-family: var(--font-mono);
          font-size: 0.62rem;
          color: var(--muted);
          letter-spacing: 0.06em;
          text-transform: uppercase;
        }
        .dark-knight-reason {
          margin-top: 0.45rem;
          font-size: 0.78rem;
          color: var(--text);
          line-height: 1.45;
        }

        /* ── DEMO SECTION ── */
        .demo-section {
          margin-top: 2.5rem;
          border-top: 1px solid var(--glass-border);
          padding-top: 1.5rem;
        }
        .demo-toggle {
          display: flex; align-items: center; gap: 0.6rem; width: 100%;
          background: none; border: none; color: var(--muted); cursor: pointer;
          font-family: var(--font-mono); font-size: 0.65rem; letter-spacing: 0.1em;
          text-transform: uppercase; padding: 0; margin-bottom: 0;
        }
        .demo-toggle:hover { color: var(--text); }
        .demo-toggle-arrow { transition: transform 0.2s; }
        .demo-toggle-arrow.open { transform: rotate(90deg); }
        .demo-table-wrap {
          margin-top: 1rem;
          overflow-x: auto;
          border-radius: 14px;
          border: 1px solid var(--glass-border);
        }
        .demo-table {
          width: 100%; border-collapse: collapse;
          font-size: 0.82rem;
        }
        .demo-table th {
          font-family: var(--font-mono); font-size: 0.6rem; letter-spacing: 0.1em;
          color: var(--muted); text-transform: uppercase;
          padding: 0.75rem 1rem; text-align: left;
          background: rgba(10,22,40,0.8);
          border-bottom: 1px solid var(--glass-border);
        }
        .demo-table td {
          padding: 0.7rem 1rem;
          border-bottom: 1px solid rgba(255,255,255,0.04);
          color: var(--text);
        }
        .demo-table tr:last-child td { border-bottom: none; }
        .demo-table tr:nth-child(even) td { background: rgba(255,255,255,0.01); }
        .demo-alert-yes {
          font-family: var(--font-mono); font-size: 0.6rem;
          color: var(--accent); background: rgba(232,200,74,0.1);
          border: 1px solid rgba(232,200,74,0.25);
          padding: 0.15rem 0.4rem; border-radius: 4px;
        }

        @media (max-width: 640px) {
          .team-selector-row { flex-direction: column; }
          .swap-btn { width: 100%; height: 34px; }
          .teams-result-row { flex-direction: column; }
          .vs-divider { width: 100%; height: 24px; }
          .meta-row { grid-template-columns: 1fr; }
          .darkscore-main { flex-direction: column; gap: 1rem; }
        }
      `}</style>

      <div className="matchup-page">
        {/* NAV */}
        <nav className="matchup-nav">
          <a href={ROUTES.APP} className="matchup-logo">DARK<span>HORSE</span></a>
          <div className="nav-actions">
            <a href={ROUTES.APP} className="btn-ghost">← Back</a>
            <button type="button" className="btn-ghost" onClick={handleLogout}>Logout</button>
          </div>
        </nav>

        <main className="matchup-main">
          {/* HEADER */}
          <div className="page-header">
            <div className="page-eyebrow">Matchup Predictor</div>
            <h1 className="page-title">Team vs <span style={{ color: 'var(--accent)' }}>Team</span></h1>
            <p className="page-sub">Select two nations and run an AI-powered probability prediction.</p>
          </div>

          {/* SESSION STATES */}
          {loadingSession && (
            <div style={{ color: 'var(--muted)', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', padding: '2rem 0' }}>
              Checking session...
            </div>
          )}
          {!!sessionError && (
            <div className="error-alert">⚠ {sessionError}</div>
          )}
          {!loadingSession && !sessionError && loadingTeams && (
            <div style={{ color: 'var(--muted)', fontFamily: 'var(--font-mono)', fontSize: '0.75rem', padding: '0 0 1rem' }}>
              Loading model-supported teams...
            </div>
          )}
          {!loadingSession && !sessionError && !!teamsError && (
            <div className="error-alert">⚠ {teamsError}</div>
          )}

          {/* BUILDER */}
          {!loadingSession && !sessionError && (
            <form onSubmit={handlePredict}>
              <div className="builder-card">
                {/* Team selectors */}
                <div className="team-selector-row">
                  <TeamSelector
                    id="team-a" label="Home Team / Team A"
                    value={teamA} onChange={(v) => { setTeamA(v); setResult(null); setHasRun(false) }}
                    exclude={teamB}
                    teams={teamOptions}
                    disabled={loadingTeams || submitting}
                  />
                  <button type="button" className="swap-btn" onClick={handleSwap} title="Swap teams" disabled={loadingTeams || submitting}>⇄</button>
                  <TeamSelector
                    id="team-b" label="Away Team / Team B"
                    value={teamB} onChange={(v) => { setTeamB(v); setResult(null); setHasRun(false) }}
                    exclude={teamA}
                    teams={teamOptions}
                    disabled={loadingTeams || submitting}
                  />
                </div>

                {/* Venue */}
                <div className="venue-row">
                  <span className="venue-label">Venue</span>
                  <div className="venue-options">
                    <button
                      type="button"
                      className={`venue-pill${neutralSite ? ' active' : ''}`}
                      onClick={() => setNeutralSite(true)}
                    >⚽ Neutral Site</button>
                    <button
                      type="button"
                      className={`venue-pill${!neutralSite ? ' active' : ''}`}
                      onClick={() => setNeutralSite(false)}
                    >🏟️ Team A Home</button>
                  </div>
                </div>

                {/* Stage */}
                <div className="venue-row">
                  <span className="venue-label">Stage</span>
                  <div className="venue-options">
                    <button
                      type="button"
                      className={`venue-pill${stageName === 'group stage' ? ' active' : ''}`}
                      onClick={() => setStageName('group stage')}
                    >Group Stage</button>
                    <button
                      type="button"
                      className={`venue-pill${stageName === 'knockout' ? ' active' : ''}`}
                      onClick={() => setStageName('knockout')}
                    >Knockout</button>
                  </div>
                </div>

                {/* Submit */}
                <button
                  type="submit"
                  className={`predict-btn${submitting ? ' loading' : ''}`}
                  disabled={submitting || loadingTeams || teamOptions.length < 2}
                >
                  {loadingTeams ? 'Loading Teams...' : submitting ? 'Running Simulation...' : '⚡ Predict Matchup'}
                </button>
              </div>

              {!!error && <div className="error-alert">⚠ {error}</div>}
            </form>
          )}

          {/* RESULTS */}
          {result && hasRun && (
            <div className="results-section">
              <div className="results-header">Prediction Results</div>

              {/* Team comparison cards */}
              <div className="teams-result-row">
                <TeamCard
                  team={result.team_a}
                  prob={result.team_a_win_prob}
                  isWinner={result.predicted_winner === result.team_a}
                  side="left"
                />
                <div className="vs-divider">VS</div>
                <TeamCard
                  team={result.team_b}
                  prob={result.team_b_win_prob}
                  isWinner={result.predicted_winner === result.team_b}
                  side="right"
                />
              </div>

              {/* Probability bars */}
              <div className="probs-card">
                <div className="probs-title">Win / Draw / Loss Breakdown</div>
                <div className="probs-bars">
                  <ProbBar
                    label={result.team_a.split(' ').pop().substring(0, 3).toUpperCase()}
                    pct={result.team_a_win_prob}
                    color="linear-gradient(90deg, #1a4fff, #2563ff)"
                  />
                  <ProbBar
                    label="DRW"
                    pct={result.draw_prob}
                    color="rgba(255,255,255,0.25)"
                  />
                  <ProbBar
                    label={result.team_b.split(' ').pop().substring(0, 3).toUpperCase()}
                    pct={result.team_b_win_prob}
                    color="linear-gradient(90deg, #e84a4a, #ff6060)"
                  />
                </div>
              </div>

              {/* Meta row: Upset Score + Confidence */}
              <div className="meta-row">
                <div className="meta-card">
                  <UpsetMeter score={result.upset_score} />
                </div>
                <div className="meta-card">
                  <div className="meta-card-label">Confidence</div>
                  <div className="meta-card-value" style={{ color: confidenceColor }}>{result.confidence}</div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.62rem', color: 'var(--muted)', marginTop: '0.3rem' }}>
                    Model certainty level
                  </div>
                </div>
              </div>

              {/* Explanation */}
              {result.explanation?.length > 0 && (
                <div className="explanation-card">
                  <div className="explanation-title">Why This Prediction</div>
                  <ul className="explanation-list">
                    {result.explanation.map((line) => (
                      <li key={line} className="explanation-item">{line}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* DarkScore Card */}
              {darkScoreResult && (() => {
                const ds = darkScoreResult
                const score = ds.dark_score
                const tier = getDarkScoreTier(score)
                const scoreColor = tier.color
                const totalElo = (ds.elo_home_pre || 0) + (ds.elo_away_pre || 0)
                const homePct = totalElo > 0 ? Math.round((ds.elo_home_pre / totalElo) * 100) : 50
                const fanTakeaways = Array.isArray(ds.fan_takeaways) && ds.fan_takeaways.length > 0
                  ? ds.fan_takeaways
                  : (Array.isArray(ds.explanations) ? ds.explanations : [])
                const darkKnight = ds.dark_knight
                return (
                  <div className="darkscore-card">
                    <div className="darkscore-header">
                      <span className="darkscore-label">DarkScore — ML Upset Model</span>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        {ds.alert && <span className="darkscore-alert-badge">⚡ UPSET ALERT</span>}
                        <span className="darkscore-tier-badge" style={{ color: tier.color }}>{ds.risk_band || tier.label}</span>
                      </div>
                    </div>

                    <div className="darkscore-main">
                      <div className="darkscore-number-wrap">
                        <span className="darkscore-number" style={{ fontSize: '4rem', color: scoreColor }}>{score}</span>
                        <span className="darkscore-of">/100</span>
                      </div>
                      <div className="darkscore-teams">
                        <div className="darkscore-team-row">Favorite: <strong>{ds.favorite_by_elo}</strong></div>
                        <div className="darkscore-team-row">Underdog: <strong>{ds.underdog_by_elo}</strong></div>
                        <div className="darkscore-team-row" style={{ marginTop: '0.2rem' }}>
                          Upset probability: <strong style={{ color: scoreColor }}>{Math.round(ds.p_final * 100)}%</strong>
                        </div>
                        <div className="darkscore-team-row">
                          Match impact: <strong>{ds.impact_level || 'Volatile'}</strong>
                        </div>
                      </div>
                    </div>

                    <div className="elo-bar-section">
                      <div className="elo-bar-labels">
                        <span>{ds.home_team} Elo {Math.round(ds.elo_home_pre)}</span>
                        <span>{ds.away_team} Elo {Math.round(ds.elo_away_pre)}</span>
                      </div>
                      <div className="elo-bar-track">
                        <div style={{ width: `${homePct}%`, height: '100%', background: 'linear-gradient(90deg, #1a4fff, #2563ff)', borderRadius: '100px 0 0 100px' }} />
                        <div style={{ width: `${100 - homePct}%`, height: '100%', background: 'linear-gradient(90deg, #e84a4a, #ff6060)', borderRadius: '0 100px 100px 0' }} />
                      </div>
                    </div>

                    <div className="darkscore-insight">
                      <div className="darkscore-insight-title">What This Means</div>
                      <div className="darkscore-insight-summary">
                        {ds.fan_summary || 'Model summary unavailable for this matchup.'}
                      </div>
                    </div>

                    {darkKnight && (
                      <div className="dark-knight-card">
                        <div className="dark-knight-label">Dark Knight</div>
                        <div className="dark-knight-player">{darkKnight.player_name || 'Data missing'}</div>
                        <div className="dark-knight-meta">
                          {(darkKnight.team || 'Data missing')} · {(darkKnight.position || 'Data missing')} · SKILL {(darkKnight.skill_score ?? 'Data missing')}
                        </div>
                        <div className="dark-knight-reason">{darkKnight.reason || 'No player-impact summary available.'}</div>
                      </div>
                    )}

                    {fanTakeaways.length > 0 && (
                      <ul className="explanation-list" style={{ marginTop: '0.5rem' }}>
                        {fanTakeaways.map((line) => (
                          <li key={line} className="explanation-item">{line}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                )
              })()}
              {darkScoreError && (
                <div className="error-alert" style={{ marginTop: '0.75rem' }}>⚠ DarkScore: {darkScoreError}</div>
              )}
            </div>
          )}

          {/* Demo Predictions */}
          {demoPredictions.length > 0 && (
            <div className="demo-section">
              <button type="button" className="demo-toggle" onClick={() => setDemoOpen(o => !o)}>
                <span className={`demo-toggle-arrow${demoOpen ? ' open' : ''}`}>▶</span>
                Demo Predictions — Top Matchups
                <span style={{ marginLeft: 'auto', color: 'var(--accent)' }}>{demoPredictions.length} matches</span>
              </button>
              {demoOpen && (
                <div className="demo-table-wrap">
                  <table className="demo-table">
                    <thead>
                      <tr>
                        <th>Home</th>
                        <th>Away</th>
                        <th>Favorite</th>
                        <th>DarkScore</th>
                        <th>Upset %</th>
                        <th>Alert</th>
                      </tr>
                    </thead>
                    <tbody>
                      {demoPredictions.map((row, i) => {
                        const score = row.dark_score
                        const scoreColor = score >= 60 ? 'var(--accent)' : score >= 40 ? '#f0a500' : '#4a8fff'
                        return (
                          <tr key={i}>
                            <td>{row.home_team}</td>
                            <td>{row.away_team}</td>
                            <td style={{ color: 'var(--muted)' }}>{row.favorite_by_elo}</td>
                            <td style={{ fontFamily: 'var(--font-display)', fontSize: '1.2rem', color: scoreColor }}>{score}</td>
                            <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>{Math.round(row.p_final * 100)}%</td>
                            <td>{row.alert ? <span className="demo-alert-yes">YES</span> : <span style={{ color: 'var(--muted)', fontSize: '0.75rem' }}>—</span>}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </>
  )
}

export default MatchupPage
