import { useState } from 'react'
import './App.css'
import './style-template.css'
import { getSupabaseClient } from './lib/supabase'
import LoggedInPage from './pages/LoggedInPage'
import LandingPage from './pages/LandingPage'
import MatchupPage from './pages/MatchupPage'
import TeamRosterPage from './pages/TeamRosterPage'
import { ROUTES } from './routes'

function AuthPage({ mode }) {
  const isLogin = mode === 'login'
  const [fullName, setFullName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [messageType, setMessageType] = useState('info')

  async function handleSubmit(event) {
    event.preventDefault()
    setMessage('')
    setMessageType('info')
    setLoading(true)

    try {
      const supabase = getSupabaseClient()

      if (isLogin) {
        const { error } = await supabase.auth.signInWithPassword({
          email,
          password,
        })

        if (error) throw error

        setMessageType('success')
        setMessage('Login successful. Redirecting...')
        window.location.href = ROUTES.APP
        return
      }

      const { error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: fullName,
          },
        },
      })

      if (error) throw error

      setMessageType('success')
      setMessage('Sign-up successful. Check your email to confirm your account.')
    } catch (error) {
      setMessageType('error')
      setMessage(error.message || 'Authentication failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="template-page">
      <div className="template-topbar">
        <a href={ROUTES.HOME} className="logo">
          UNDER<span>DOG</span>
        </a>
      </div>

      <main className="template-main">
        <section className="template-card">
          <p className="section-label">Account Access</p>
          <h1 className="template-title">{isLogin ? 'Login' : 'Sign Up'}</h1>
          <p className="template-subtitle">
            {isLogin
              ? 'Sign in to view your upset predictions and picks.'
              : 'Create your account to start tracking upset predictions.'}
          </p>

          <form className="template-form" onSubmit={handleSubmit}>
            {!isLogin && (
              <>
                <label className="template-label" htmlFor="name">
                  Full Name
                </label>
                <input
                  className="template-input"
                  id="name"
                  type="text"
                  placeholder="Your name"
                  value={fullName}
                  onChange={(event) => setFullName(event.target.value)}
                  required
                />
              </>
            )}
            <label className="template-label" htmlFor="email">
              Email
            </label>
            <input
              className="template-input"
              id="email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
            <label className="template-label" htmlFor="password">
              Password
            </label>
            <input
              className="template-input"
              id="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              minLength={6}
              required
            />
            <button
              type="submit"
              className={`template-button ${isLogin ? 'template-button-secondary' : 'template-button-primary'}`}
              disabled={loading}
            >
              {loading ? 'Please wait...' : isLogin ? 'Login' : 'Sign Up'}
            </button>
          </form>

          {message && (
            <p className={`template-alert template-alert-${messageType}`}>
              {message}
            </p>
          )}

          <p className="template-switch">
            {isLogin ? "Don't have an account? " : 'Already have an account? '}
            <a
              className="template-link"
              href={isLogin ? ROUTES.SIGNUP : ROUTES.LOGIN}
            >
              {isLogin ? 'Sign Up' : 'Login'}
            </a>
          </p>
        </section>
      </main>
    </div>
  )
}

function App() {
  const path = window.location.pathname.replace(/\/+$/, '') || ROUTES.HOME

  if (path === ROUTES.LOGIN) {
    return <AuthPage mode="login" />
  }

  if (path === ROUTES.SIGNUP) {
    return <AuthPage mode="signup" />
  }

  if (path === ROUTES.APP) {
    return <LoggedInPage />
  }

  if (path === ROUTES.MATCHUP) {
    return <MatchupPage />
  }

  if (path === ROUTES.ROSTERS) {
    return <TeamRosterPage />
  }

  return <LandingPage />
}

export default App
