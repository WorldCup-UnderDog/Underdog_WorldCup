const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const FIFA_RANKINGS = {
  Spain: 1,
  Argentina: 2,
  France: 3,
  England: 4,
  Brazil: 5,
  Portugal: 6,
  Netherlands: 7,
  Belgium: 8,
  Germany: 9,
  Croatia: 10,
  Morocco: 11,
  Colombia: 12,
  'United States': 13,
  Mexico: 14,
  Uruguay: 15,
  Switzerland: 16,
  Japan: 17,
  Senegal: 18,
  Iran: 19,
  'South Korea': 20,
  Ecuador: 21,
  Austria: 22,
  Australia: 23,
  Canada: 24,
  Norway: 25,
  Panama: 26,
  Egypt: 27,
  Algeria: 28,
  Scotland: 29,
  Paraguay: 30,
  Tunisia: 31,
  'Ivory Coast': 32,
  Uzbekistan: 33,
  Qatar: 34,
  'Saudi Arabia': 35,
  'South Africa': 36,
  Jordan: 37,
  'Cape Verde': 38,
  Ghana: 39,
  'Curaçao': 40,
  Haiti: 41,
  'New Zealand': 42,
}

export async function fetchTeamRoster(teamName) {
  try {
    const res = await fetch(`${BASE_URL}/players?nation=${encodeURIComponent(teamName.toLowerCase())}`)
    if (!res.ok) throw new Error('Failed to fetch')
    const players = await res.json()

    if (!players.length) return null

    // Shape the data to match what TeamRosterDetailPage expects
    return {
      team: teamName,
      stats: {
        confederation: getConfederation(teamName),
        fifa_rank: FIFA_RANKINGS[teamName],
        world_cup_titles: getWorldCupTitles(teamName),
        recent_form: 'W-D-W-L-W',
      },
      players: players.map((p, i) => ({
        number: i + 1,
        name: p.name,
        nation: p.nation,
        position: p.best_position,
        overall: p.overall_rating,
        potential: p.potential,
        age: p.age,
        value: p.value,
        // Raw stats for radar chart later
        acceleration: p.acceleration,
        sprint_speed: p.sprint_speed,
        dribbling: p.dribbling,
        finishing: p.finishing,
        short_passing: p.short_passing,
        long_passing: p.long_passing,
        total_attacking: p.total_attacking,
        total_skill: p.total_skill,
        total_movement: p.total_movement,
        total_power: p.total_power,
        total_mentality: p.total_mentality,
        total_defending: p.total_defending,
        total_goalkeeping: p.total_goalkeeping,
        reactions: p.reactions,
        heading_accuracy: p.heading_accuracy,
        playstyles: [p.playstyles, p.playstyles2, p.playstyles3].filter(Boolean),
      })),
      starting_xi: players.slice(0, 11).map((p, i) => ({
        number: i + 1,
        name: p.name,
        position: p.best_position,
        overall: p.overall_rating,
      })),
    }
  } catch (err) {
    console.error('fetchTeamRoster error:', err)
    return null
  }
}

function getConfederation(team) {
  const UEFA = ['France','Germany','Spain','England','Portugal','Netherlands','Belgium','Croatia','Austria','Switzerland','Scotland','Norway']
  const CONMEBOL = ['Argentina','Brazil','Colombia','Uruguay','Ecuador','Paraguay']
  const CAF = ['Morocco','Senegal','Algeria','Egypt','Ghana','Ivory Coast','Tunisia','South Africa','Cape Verde']
  const AFC = ['Japan','South Korea','Iran','Saudi Arabia','Australia','Qatar','Jordan','Uzbekistan']
  const CONCACAF = ['United States','Mexico','Canada','Panama','Haiti','Curaçao']
  if (UEFA.includes(team)) return 'UEFA'
  if (CONMEBOL.includes(team)) return 'CONMEBOL'
  if (CAF.includes(team)) return 'CAF'
  if (AFC.includes(team)) return 'AFC'
  if (CONCACAF.includes(team)) return 'CONCACAF'
  return 'FIFA'
}

function getWorldCupTitles(team) {
  const titles = { 'Brazil': 5, 'Germany': 4, 'Italy': 4, 'France': 2, 'Argentina': 3, 'Uruguay': 2, 'England': 1, 'Spain': 1 }
  return titles[team] ?? 0
}