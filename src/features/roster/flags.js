import { TEAM_TO_FLAG_CODE } from './constants'

const FLAG_SVGS = import.meta.glob('../../assets/flags/*.svg', { eager: true, import: 'default' })
const VALID_FLAG_CODES = new Set(Object.values(TEAM_TO_FLAG_CODE))

export function getFlagSrcByCode(code) {
  const normalizedCode = normalizeFlagCode(code)
  if (!normalizedCode) return null
  return FLAG_SVGS[`../../assets/flags/${normalizedCode}.svg`] || null
}

export function normalizeFlagCode(value) {
  const raw = String(value || '').trim().toLowerCase()
  if (!raw) return ''
  if (VALID_FLAG_CODES.has(raw)) return raw

  const withoutQuery = raw.split('?')[0].split('#')[0]
  const filename = withoutQuery.slice(withoutQuery.lastIndexOf('/') + 1)
  if (!filename.endsWith('.svg')) return ''

  let candidate = filename.replace(/\.svg$/, '')
  if (VALID_FLAG_CODES.has(candidate)) return candidate

  // Supports previously persisted hashed build URLs like "gb-eng-ab12cd.svg".
  while (candidate.includes('-')) {
    candidate = candidate.replace(/-[^-]+$/, '')
    if (VALID_FLAG_CODES.has(candidate)) return candidate
  }

  return ''
}

export function getFlagSrcFromStoredValue(value) {
  return getFlagSrcByCode(normalizeFlagCode(value))
}

export function getFlagSrc(team) {
  const code = TEAM_TO_FLAG_CODE[team]
  return getFlagSrcByCode(code)
}
