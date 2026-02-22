const POSITION_ALIASES = {
  GOALKEEPER: 'GK',
  RCB: 'CB',
  LCB: 'CB',
  RDM: 'DM',
  LDM: 'DM',
  RCM: 'CM',
  LCM: 'CM',
  CAM: 'AM',
  LF: 'LW',
  RF: 'RW',
  STRIKER: 'ST',
}

const DEFENSE_POSITIONS = new Set(['RB', 'RWB', 'CB', 'LB', 'LWB', 'SW'])
const MIDFIELD_POSITIONS = new Set(['DM', 'CM', 'AM', 'RM', 'LM'])
const ATTACK_POSITIONS = new Set(['RW', 'LW', 'CF', 'ST', 'SS'])

const SORT_ORDER = {
  RB: 1,
  RWB: 2,
  CB: 3,
  SW: 4,
  LB: 5,
  LWB: 6,
  RM: 1,
  DM: 2,
  CM: 3,
  AM: 4,
  LM: 5,
  RW: 1,
  SS: 2,
  CF: 3,
  ST: 4,
  LW: 5,
}

// Line priority for sorting outfield players defender → midfielder → attacker
const LINE_PRIORITY = { DEF: 1, MID: 2, ATT: 3 }

//Best choice of formation for each team based on their typical playing style and historical data
export const TEAM_FORMATIONS = {
  // 4-3-3
  Spain: '4-3-3',
  Brazil: '4-3-3',
  Netherlands: '4-3-3',
  Portugal: '4-3-3',
  Morocco: '4-3-3',
  Colombia: '4-3-3',
  Japan: '4-3-3',
  Ecuador: '4-3-3',
  Norway: '4-3-3',
  Algeria: '4-3-3',
  Scotland: '4-3-3',
  Tunisia: '4-3-3',
  'Ivory Coast': '4-3-3',
  Uzbekistan: '4-3-3',
  'Cape Verde': '4-3-3',
  Ghana: '4-3-3',
  // 4-2-3-1
  Argentina: '4-2-3-1',
  France: '4-2-3-1',
  England: '4-2-3-1',
  Belgium: '4-2-3-1',
  Germany: '4-2-3-1',
  Croatia: '4-2-3-1',
  Switzerland: '4-2-3-1',
  Mexico: '4-2-3-1',
  Senegal: '4-2-3-1',
  Iran: '4-2-3-1',
  'South Korea': '4-2-3-1',
  Austria: '4-2-3-1',
  Canada: '4-2-3-1',
  Panama: '4-2-3-1',
  Egypt: '4-2-3-1',
  'South Africa': '4-2-3-1',
  Jordan: '4-2-3-1',
  'Saudi Arabia': '4-2-3-1',
  'Curaçao': '4-2-3-1',
  Haiti: '4-2-3-1',
  'New Zealand': '4-2-3-1',
  // 4-4-2
  'United States': '4-4-2',
  Uruguay: '4-4-2',
  Australia: '4-4-2',
  Paraguay: '4-4-2',
  Qatar: '4-4-2',
}

function parseFormation(formation) {
  const parts = formation.split('-').map(Number)
  if (parts.length === 4) {
    // e.g. 4-2-3-1 → def=4, dm=2, mid=3, att=1
    return { def: parts[0], dm: parts[1], mid: parts[2], att: parts[3] }
  }
  // e.g. 4-3-3 or 4-4-2 → def=4, dm=0, mid, att
  return { def: parts[0] ?? 4, dm: 0, mid: parts[1] ?? 3, att: parts[2] ?? 3 }
}

export function normalizePosition(position) {
  if (!position) return 'CM'
  const raw = String(position).trim().toUpperCase().replace(/\s+/g, '')
  const token = raw.split('/')[0]
  if (POSITION_ALIASES[token]) return POSITION_ALIASES[token]
  if (token === 'GK') return 'GK'
  if (DEFENSE_POSITIONS.has(token)) return token
  if (MIDFIELD_POSITIONS.has(token)) return token
  if (ATTACK_POSITIONS.has(token)) return token
  return 'CM'
}

function getLine(normalizedPosition) {
  if (normalizedPosition === 'GK') return 'GK'
  if (DEFENSE_POSITIONS.has(normalizedPosition)) return 'DEF'
  if (MIDFIELD_POSITIONS.has(normalizedPosition)) return 'MID'
  if (ATTACK_POSITIONS.has(normalizedPosition)) return 'ATT'
  return 'MID'
}

function sortLine(players) {
  return [...players].sort((a, b) => {
    const aRank = SORT_ORDER[a.normalized_position] || 99
    const bRank = SORT_ORDER[b.normalized_position] || 99
    if (aRank !== bRank) return aRank - bRank
    return a.name.localeCompare(b.name)
  })
}

export function buildStartingXIFormation(players, formation = '4-3-3') {
  const xi = Array.isArray(players) ? players.slice(0, 11) : []
  if (xi.length === 0) {
    return {
      formation: '0-0-0',
      lines: { gk: [], defense: [], dm: [], midfield: [], attack: [] },
    }
  }

  const { def: targetDef, dm: targetDm, mid: targetMid, att: targetAtt } = parseFormation(formation)

  // Normalize positions on all players
  const tagged = xi.map((player) => {
    const normalized_position = normalizePosition(player.position)
    const line = getLine(normalized_position)
    return { ...player, normalized_position, line }
  })

  // Extract GK
  const gkIndex = tagged.findIndex((p) => p.line === 'GK')
  let gk
  if (gkIndex >= 0) {
    ;[gk] = tagged.splice(gkIndex, 1)
  } else {
    gk = { ...tagged[0], normalized_position: 'GK', line: 'GK' }
    tagged.splice(0, 1)
  }

  // Sort remaining 10 by natural line order: DEF → MID → ATT
  tagged.sort((a, b) => {
    const pa = LINE_PRIORITY[a.line] ?? 2
    const pb = LINE_PRIORITY[b.line] ?? 2
    if (pa !== pb) return pa - pb
    return (SORT_ORDER[a.normalized_position] || 99) - (SORT_ORDER[b.normalized_position] || 99)
  })

  // Assign players to lines in order, filling each to its target count
  const defense = tagged.splice(0, targetDef)
  const dm = tagged.splice(0, targetDm)
  const midfield = tagged.splice(0, targetMid)
  const attack = tagged.splice(0, targetAtt)

  return {
    formation,
    lines: {
      gk: [gk],
      defense: sortLine(defense),
      dm: sortLine(dm),
      midfield: sortLine(midfield),
      attack: sortLine(attack),
    },
  }
}
