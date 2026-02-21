export const TEAMS = [
  'Canada', 'Mexico', 'United States',
  'Australia', 'Iran', 'Japan', 'Jordan', 'South Korea', 'Qatar', 'Saudi Arabia', 'Uzbekistan',
  'Algeria', 'Cape Verde', 'Egypt', 'Ghana', 'Ivory Coast', 'Morocco', 'Senegal', 'South Africa', 'Tunisia',
  'Curaçao', 'Haiti', 'Panama',
  'Argentina', 'Brazil', 'Colombia', 'Ecuador', 'Paraguay', 'Uruguay',
  'New Zealand',
  'Austria', 'Belgium', 'Croatia', 'England', 'France', 'Germany', 'Netherlands',
  'Norway', 'Portugal', 'Scotland', 'Spain', 'Switzerland',
]

const FLAG_MAP = {
  Canada: '🇨🇦', Mexico: '🇲🇽', 'United States': '🇺🇸',
  Australia: '🇦🇺', Iran: '🇮🇷', Japan: '🇯🇵', Jordan: '🇯🇴',
  'South Korea': '🇰🇷', Qatar: '🇶🇦', 'Saudi Arabia': '🇸🇦', Uzbekistan: '🇺🇿',
  Algeria: '🇩🇿', 'Cape Verde': '🇨🇻', Egypt: '🇪🇬', Ghana: '🇬🇭',
  'Ivory Coast': '🇨🇮', Morocco: '🇲🇦', Senegal: '🇸🇳', 'South Africa': '🇿🇦', Tunisia: '🇹🇳',
  Curaçao: '🇨🇼', Haiti: '🇭🇹', Panama: '🇵🇦',
  Argentina: '🇦🇷', Brazil: '🇧🇷', Colombia: '🇨🇴', Ecuador: '🇪🇨',
  Paraguay: '🇵🇾', Uruguay: '🇺🇾', 'New Zealand': '🇳🇿',
  Austria: '🇦🇹', Belgium: '🇧🇪', Croatia: '🇭🇷', England: '🏴',
  France: '🇫🇷', Germany: '🇩🇪', Netherlands: '🇳🇱', Norway: '🇳🇴',
  Portugal: '🇵🇹', Scotland: '🏴', Spain: '🇪🇸', Switzerland: '🇨🇭',
}

export function getFlag(team) {
  return FLAG_MAP[team] || '🏳️'
}
