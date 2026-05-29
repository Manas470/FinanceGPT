/** Severity / Risk level badge */
import { Severity, RiskLevel } from '../../types'

const SEVERITY_STYLES: Record<string, string> = {
  info:     'bg-blue-100 text-blue-800',
  low:      'bg-green-100 text-green-800',
  medium:   'bg-yellow-100 text-yellow-800',
  high:     'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800 font-bold',
}

interface Props {
  level: Severity | RiskLevel | string
  size?: 'sm' | 'md'
}

export function SeverityBadge({ level, size = 'sm' }: Props) {
  const styles = SEVERITY_STYLES[level] || 'bg-gray-100 text-gray-800'
  const textSize = size === 'sm' ? 'text-xs' : 'text-sm'
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full ${textSize} ${styles} uppercase tracking-wide`}>
      {level}
    </span>
  )
}
