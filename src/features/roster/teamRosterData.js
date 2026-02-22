import { WORLD_CUP_TEAMS } from './constants'

const STARTING_XI_POSITIONS = ['GK', 'RB', 'CB', 'CB', 'LB', 'DM', 'CM', 'AM', 'RW', 'ST', 'LW']
const BENCH_POSITIONS = ['GK', 'RB', 'CB', 'LB', 'DM', 'CM', 'CM', 'AM', 'RW', 'LW', 'ST', 'ST']

const TEAM_TITLES = {
  Argentina: 3,
  Brazil: 5,
  England: 1,
  France: 2,
  Germany: 4,
  Spain: 1,
  Uruguay: 2,
}

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

const CONFEDERATIONS = {
  AFC: ['Australia', 'Iran', 'Japan', 'Jordan', 'Qatar', 'Saudi Arabia', 'South Korea', 'Uzbekistan'],
  CAF: ['Algeria', 'Cape Verde', 'Egypt', 'Ghana', 'Ivory Coast', 'Morocco', 'Senegal', 'South Africa', 'Tunisia'],
  CONCACAF: ['Canada', 'Curaçao', 'Haiti', 'Mexico', 'Panama', 'United States'],
  CONMEBOL: ['Argentina', 'Brazil', 'Colombia', 'Ecuador', 'Paraguay', 'Uruguay'],
  OFC: ['New Zealand'],
  UEFA: ['Austria', 'Belgium', 'Croatia', 'England', 'France', 'Germany', 'Netherlands', 'Norway', 'Portugal', 'Scotland', 'Spain', 'Switzerland'],
}

function getConfederation(team) {
  const entry = Object.entries(CONFEDERATIONS).find(([, teams]) => teams.includes(team))
  return entry ? entry[0] : 'Unknown'
}

function buildPlayer(team, number, position) {
  return {
    number,
    name: `${team} Player ${number}`,
    position,
    overall: 70 + ((number - 1) % 20),
    stats: {
      caps: 10 + (number * 2),
      goals: position === 'ST' || position === 'RW' || position === 'LW' ? Math.max(1, Math.floor(number / 3)) : 0,
      assists: position === 'AM' || position === 'CM' || position === 'RW' || position === 'LW' ? Math.floor(number / 4) : 0,
    },
  }
}

function buildStartingXI(team) {
  return STARTING_XI_POSITIONS.map((position, index) => buildPlayer(team, index + 1, position))
}

function buildPlayers(team, startingXI) {
  const benchPlayers = BENCH_POSITIONS.map((position, index) => buildPlayer(team, 12 + index, position))
  return [...startingXI, ...benchPlayers]
}

export const STATIC_TEAM_ROSTER_DATA = Object.fromEntries(
  WORLD_CUP_TEAMS.map((team) => {
    const starting_xi = buildStartingXI(team)
    return [team, {
      team,
      stats: {
        confederation: getConfederation(team),
        fifa_rank: FIFA_RANKINGS[team],
        world_cup_titles: TEAM_TITLES[team] || 0,
        recent_form: 'W-D-W-L-W',
      },
      starting_xi,
      players: buildPlayers(team, starting_xi),
    }]
  })
)
