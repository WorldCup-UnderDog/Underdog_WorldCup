export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  SIGNUP: '/signup',
  APP: '/app',
  PROFILE: '/app/profile',
  MATCHUP: '/app/matchup',
  DARKSCORE_FAQ: '/app/darkscore-faq',
  ROSTERS: '/app/rosters',
}

export function getTeamRosterRoute(teamName) {
  return `${ROUTES.ROSTERS}/${encodeURIComponent(teamName)}`
}

export function getTeamFromRosterPath(pathname) {
  const prefix = `${ROUTES.ROSTERS}/`
  if (!pathname.startsWith(prefix)) return ''

  const encodedTeam = pathname.slice(prefix.length)
  if (!encodedTeam) return ''

  try {
    return decodeURIComponent(encodedTeam)
  } catch {
    return ''
  }
}
