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

export function buildStartingXIFormation(players) {
  const xi = Array.isArray(players) ? players.slice(0, 11) : []
  if (xi.length === 0) {
    return {
      formation: '0-0-0',
      lines: { gk: [], defense: [], midfield: [], attack: [] },
    }
  }

  let gk = null
  const defense = []
  const midfield = []
  const attack = []

  xi.forEach((player) => {
    const normalized_position = normalizePosition(player.position)
    const normalizedPlayer = { ...player, normalized_position }
    const line = getLine(normalized_position)

    if (line === 'GK') {
      if (!gk) {
        gk = normalizedPlayer
      } else {
        defense.push({ ...normalizedPlayer, normalized_position: 'CB' })
      }
      return
    }

    if (line === 'DEF') {
      defense.push(normalizedPlayer)
      return
    }

    if (line === 'MID') {
      midfield.push(normalizedPlayer)
      return
    }

    attack.push(normalizedPlayer)
  })

  if (!gk) {
    const fallback = defense.shift() || midfield.shift() || attack.shift() || xi[0]
    gk = { ...fallback, normalized_position: 'GK' }
  }

  const sortedDefense = sortLine(defense)
  const sortedMidfield = sortLine(midfield)
  const sortedAttack = sortLine(attack)
  const formation = `${sortedDefense.length}-${sortedMidfield.length}-${sortedAttack.length}`

  return {
    formation,
    lines: {
      gk: [gk],
      defense: sortedDefense,
      midfield: sortedMidfield,
      attack: sortedAttack,
    },
  }
}
