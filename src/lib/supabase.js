import { createClient } from '@supabase/supabase-js'

let client

export function getSupabaseClient() {
  if (client) return client

  const url = import.meta.env.VITE_SUPABASE_URL
  const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

  if (!url || !anonKey) {
    throw new Error(
      'Missing Supabase env vars. Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in .env'
    )
  }

  client = createClient(url, anonKey)
  return client
}
