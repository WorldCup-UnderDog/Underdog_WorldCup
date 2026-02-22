import { useEffect, useMemo, useState } from 'react'
import { getSupabaseClient } from '../lib/supabase'
import { fetchProfile, isProfileComplete, upsertProfile } from '../lib/profile'
import { ROUTES } from '../routes'
import { TEAM_TO_FLAG_CODE, WORLD_CUP_TEAMS } from '../features/roster/constants'
import { getFlagSrcByCode, normalizeFlagCode } from '../features/roster/flags'

const TEAM_OPTIONS = [...WORLD_CUP_TEAMS].sort((a, b) => a.localeCompare(b))
const CODE_TO_TEAM = Object.fromEntries(
  Object.entries(TEAM_TO_FLAG_CODE).map(([team, code]) => [code, team])
)

function ProfilePage() {
  const [sessionLoading, setSessionLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  const [userId, setUserId] = useState('')
  const [email, setEmail] = useState('')
  const [onboarding, setOnboarding] = useState(false)

  const [fullName, setFullName] = useState('')
  const [username, setUsername] = useState('')
  const [favoriteTeam, setFavoriteTeam] = useState('')
  const [flag, setFlag] = useState('')

  const selectedFlagSrc = useMemo(() => getFlagSrcByCode(flag), [flag])

  useEffect(() => {
    let mounted = true

    async function load() {
      setSessionLoading(true)
      setError('')
      try {
        const params = new URLSearchParams(window.location.search)
        const isOnboarding = params.get('onboarding') === '1'
        if (mounted) setOnboarding(isOnboarding)

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

        const user = session.user
        const profile = await fetchProfile(user.id).catch(() => null)

        const metaName = String(user.user_metadata?.full_name || '').trim()
        const profileFlagUrl = String(profile?.flag_url || profile?.flag || '').trim()
        const inferredFlag = normalizeFlagCode(profileFlagUrl)
        const inferredTeam = CODE_TO_TEAM[inferredFlag] || ''

        if (mounted) {
          setUserId(user.id)
          setEmail(user.email || '')
          setFullName(String(profile?.full_name || metaName))
          setUsername(String(profile?.username || ''))
          setFavoriteTeam(inferredTeam)
          setFlag(inferredFlag)
        }
      } catch (err) {
        if (mounted) setError(err.message || 'Failed to load profile')
      } finally {
        if (mounted) setSessionLoading(false)
      }
    }

    load()
    return () => {
      mounted = false
    }
  }, [])

  function handleTeamSelect(team) {
    const nextFlag = TEAM_TO_FLAG_CODE[team] || ''
    setFavoriteTeam(team)
    setFlag(nextFlag)
    setError('')
  }

  async function handleLogout() {
    try {
      const supabase = getSupabaseClient()
      await supabase.auth.signOut()
    } finally {
      window.location.href = ROUTES.HOME
    }
  }

  async function handleSave(event) {
    event.preventDefault()
    setError('')
    setMessage('')

    const normalizedUsername = username.trim().toLowerCase()
    const normalizedFullName = fullName.trim()

    if (!normalizedFullName) {
      setError('Full name is required.')
      return
    }
    if (!normalizedUsername) {
      setError('Username is required.')
      return
    }
    if (!/^[a-z0-9_]+$/.test(normalizedUsername)) {
      setError('Username can only contain lowercase letters, numbers, and underscores.')
      return
    }
    if (!favoriteTeam || !flag) {
      setError('Please choose a country flag for your profile avatar.')
      return
    }

    setSaving(true)
    try {
      const payload = {
        id: userId,
        full_name: normalizedFullName,
        username: normalizedUsername,
        flag_url: flag,
      }
      const saved = await upsertProfile(payload)

      setMessage('Profile saved.')
      setUsername(String(saved.username || normalizedUsername))

      if (onboarding && isProfileComplete(saved)) {
        window.location.href = ROUTES.APP
      }
    } catch (err) {
      setError(err.message || 'Failed to save profile')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="template-page">
      <div className="template-topbar dashboard-topbar">
        <a href={ROUTES.HOME} className="logo">
          UNDER<span>DOG</span>
        </a>
        <div className="topbar-actions">
          <a className="btn-ghost" href={ROUTES.APP}>← Back</a>
          <button type="button" className="btn-ghost" onClick={handleLogout}>Logout</button>
        </div>
      </div>

      <main className="template-main dashboard-main">
        <section className="template-card dashboard-card profile-card">
          <p className="section-label">Profile</p>
          <h1 className="template-title">Edit Profile</h1>
          <p className="template-subtitle">
            {onboarding
              ? 'Complete your profile to finish onboarding.'
              : 'Update your public profile details.'}
          </p>

          {sessionLoading && <p className="template-subtitle">Loading profile...</p>}
          {!!error && <p className="template-alert template-alert-error">{error}</p>}
          {!!message && <p className="template-alert template-alert-success">{message}</p>}

          {!sessionLoading && (
            <form className="profile-form" onSubmit={handleSave}>
              <label className="template-label" htmlFor="profile-email">Email</label>
              <input id="profile-email" className="template-input" type="email" value={email} disabled />

              <label className="template-label" htmlFor="profile-full-name">Full Name</label>
              <input
                id="profile-full-name"
                className="template-input"
                type="text"
                value={fullName}
                onChange={(event) => setFullName(event.target.value)}
                maxLength={80}
                required
              />

              <label className="template-label" htmlFor="profile-username">Username</label>
              <input
                id="profile-username"
                className="template-input"
                type="text"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                placeholder="your_handle"
                maxLength={30}
                required
              />

              <div className="profile-avatar-row">
                <div>
                  <p className="template-label">Avatar Flag</p>
                  <div className="profile-avatar-preview">
                    {selectedFlagSrc ? (
                      <img src={selectedFlagSrc} className="profile-avatar-flag" alt="Selected flag avatar" />
                    ) : (
                      <span className="profile-avatar-fallback" aria-hidden="true">🏳️</span>
                    )}
                    <div>
                      <p className="profile-avatar-title">{favoriteTeam || 'No country selected'}</p>
                      <p className="profile-avatar-meta">Country flag avatar</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="profile-flag-picker">
                <p className="template-label">Choose Country</p>
                <div className="profile-flag-grid">
                  {TEAM_OPTIONS.map((team) => {
                    const code = TEAM_TO_FLAG_CODE[team]
                    const src = getFlagSrcByCode(code)
                    const isActive = favoriteTeam === team
                    return (
                      <button
                        key={team}
                        type="button"
                        className={`profile-flag-option${isActive ? ' active' : ''}`}
                        onClick={() => handleTeamSelect(team)}
                      >
                        {src ? (
                          <img src={src} alt={`${team} flag`} className="profile-flag-option-image" loading="lazy" />
                        ) : (
                          <span className="profile-flag-option-fallback" aria-hidden="true">🏳️</span>
                        )}
                        <span className="profile-flag-option-name">{team}</span>
                      </button>
                    )
                  })}
                </div>
              </div>

              <button type="submit" className="template-button template-button-primary" disabled={saving}>
                {saving ? 'Saving...' : onboarding ? 'Save & Continue' : 'Save Profile'}
              </button>
            </form>
          )}
        </section>
      </main>
    </div>
  )
}

export default ProfilePage
