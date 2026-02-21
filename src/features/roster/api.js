import { STATIC_TEAM_ROSTER_DATA } from './teamRosterData'

export async function fetchTeamRoster(teamName) {
  const payload = STATIC_TEAM_ROSTER_DATA[teamName]
  return payload || null
}
