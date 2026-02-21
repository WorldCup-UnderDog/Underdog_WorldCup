import { TEAM_TO_FLAG_CODE } from './constants'

const FLAG_SVGS = import.meta.glob('../../assets/flags/*.svg', { eager: true, import: 'default' })

export function getFlagSrc(team) {
  const code = TEAM_TO_FLAG_CODE[team]
  if (!code) return null
  return FLAG_SVGS[`../../assets/flags/${code}.svg`] || null
}
