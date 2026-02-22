import { useEffect, useMemo, useState } from 'react'
import { fetchProfile } from '../../../lib/profile'
import { getSupabaseClient } from '../../../lib/supabase'
import { getFlagSrcByCode, normalizeFlagCode } from '../../roster/flags'
import { ROUTES } from '../../../routes'

function getDisplayName(profile, user) {
  const profileName = String(profile?.full_name || '').trim()
  if (profileName) return profileName

  const metaName = String(user?.user_metadata?.full_name || '').trim()
  if (metaName) return metaName

  const email = String(user?.email || '')
  if (email.includes('@')) return email.split('@')[0]
  return 'Unknown user'
}

export default function useMyProfile() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [user, setUser] = useState(null)
  const [profile, setProfile] = useState(null)

  useEffect(() => {
    let mounted = true

    async function load() {
      setLoading(true)
      setError('')

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

        const profileData = await fetchProfile(session.user.id).catch(() => null)

        if (!mounted) return
        setUser(session.user)
        setProfile(profileData)
      } catch (err) {
        if (mounted) setError(err.message || 'Failed to load profile data')
      } finally {
        if (mounted) setLoading(false)
      }
    }

    load()
    return () => {
      mounted = false
    }
  }, [])

  return useMemo(() => {
    const email = String(user?.email || '').trim()
    const displayName = getDisplayName(profile, user)
    const username = String(profile?.username || '').trim()
    const flagCode = normalizeFlagCode(profile?.flag_url || profile?.flag)
    const flagSrc = getFlagSrcByCode(flagCode)

    const missingFields = []
    if (!String(profile?.full_name || '').trim()) missingFields.push('full name')
    if (!username) missingFields.push('username')
    if (!flagCode) missingFields.push('flag avatar')

    return {
      loading,
      error,
      email,
      displayName,
      username,
      flagCode,
      flagSrc,
      profileComplete: missingFields.length === 0,
      missingFields,
    }
  }, [loading, error, user, profile])
}
