export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  SIGNUP: '/signup',
  APP: '/app',
  MATCHUP: '/app/matchup',
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
