/** Circular health score gauge */
interface ScoreGaugeProps {
  score: number | null
  label: string
  size?: number
}

const getScoreColor = (score: number) => {
  if (score >= 80) return '#10b981' // green
  if (score >= 60) return '#f59e0b' // amber
  if (score >= 40) return '#f97316' // orange
  return '#ef4444' // red
}

export function ScoreGauge({ score, label, size = 80 }: ScoreGaugeProps) {
  if (score === null) return (
    <div className="flex flex-col items-center">
      <div style={{ width: size, height: size }} className="rounded-full border-4 border-gray-200 flex items-center justify-center bg-gray-50">
        <span className="text-gray-400 text-xs">N/A</span>
      </div>
      <span className="text-xs text-gray-500 mt-1 text-center">{label}</span>
    </div>
  )

  const color = getScoreColor(score)
  const radius = (size - 8) / 2
  const circumference = 2 * Math.PI * radius
  const strokeDash = (score / 100) * circumference

  return (
    <div className="flex flex-col items-center">
      <div style={{ width: size, height: size }} className="relative">
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={size / 2} cy={size / 2} r={radius}
            fill="none" stroke="#e5e7eb" strokeWidth={6}
          />
          <circle
            cx={size / 2} cy={size / 2} r={radius}
            fill="none" stroke={color} strokeWidth={6}
            strokeDasharray={`${strokeDash} ${circumference}`}
            strokeLinecap="round"
            style={{ transition: 'stroke-dasharray 0.8s ease' }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="font-bold text-gray-800" style={{ fontSize: size * 0.22 }}>
            {Math.round(score)}
          </span>
        </div>
      </div>
      <span className="text-xs text-gray-500 mt-1 text-center font-medium">{label}</span>
    </div>
  )
}
