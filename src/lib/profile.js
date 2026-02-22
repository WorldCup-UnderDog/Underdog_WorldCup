import { getSupabaseClient } from './supabase'
import { normalizeFlagCode } from '../features/roster/flags'

export function isProfileComplete(profile) {
  if (!profile) return false

  const fullName = String(profile.full_name || '').trim()
  const username = String(profile.username || '').trim()
  const flagCode = normalizeFlagCode(profile.flag_url || profile.flag)

  return Boolean(fullName && username && flagCode)
}

export async function fetchProfile(userId) {
  const supabase = getSupabaseClient()
  const { data, error } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', userId)
    .maybeSingle()

  if (error) throw error
  return data
}

export async function upsertProfile(profilePayload) {
  const supabase = getSupabaseClient()
  const { data, error } = await supabase
    .from('profiles')
    .upsert(profilePayload, { onConflict: 'id' })
    .select()
    .single()

  if (error) throw error
  return data
}
