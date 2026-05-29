/** CFO Dashboard — main metrics overview */
import { useQuery } from '@tanstack/react-query'
import { auditApi } from '../services/api'
import { DashboardMetrics, Anomaly, AuditReport } from '../types'
import { ScoreGauge } from '../components/ui/ScoreGauge'
import { SeverityBadge } from '../components/ui/SeverityBadge'
import { Link } from 'react-router-dom'

function KPICard({ label, value, icon, color }: { label: string; value: string | number; icon: string; color: string }) {
  return (
    <div className={`bg-white rounded-xl border border-gray-100 shadow-sm p-5`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">{label}</p>
          <p className={`text-3xl font-bold mt-1 ${color}`}>{value}</p>
        </div>
        <span className="text-4xl">{icon}</span>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const { data, isLoading, error } = useQuery<DashboardMetrics>({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const { data } = await auditApi.dashboard()
      return data
    },
    refetchInterval: 30000,
  })

  if (isLoading) return (
    <div className="flex-1 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin text-4xl mb-3">⚙️</div>
        <p className="text-gray-500">Loading dashboard...</p>
      </div>
    </div>
  )

  if (error) return (
    <div className="flex-1 flex items-center justify-center">
      <div className="text-center text-red-500">
        <p className="text-2xl mb-2">⚠️</p>
        <p>Failed to load dashboard data</p>
        <Link to="/documents" className="text-blue-600 text-sm mt-2 block">Upload documents to get started →</Link>
      </div>
    </div>
  )

  const metrics = data || {
    total_documents: 0, total_reports: 0, open_anomalies: 0,
    critical_anomalies: 0, avg_health_score: null,
    recent_reports: [], recent_anomalies: [],
  }

  return (
    <div className="flex-1 p-8 overflow-auto bg-gray-50">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">CFO Audit Dashboard</h1>
        <p className="text-gray-500 text-sm mt-1">AI-powered financial health overview</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <KPICard label="Documents" value={metrics.total_documents} icon="📁" color="text-blue-600" />
        <KPICard label="Audit Reports" value={metrics.total_reports} icon="📊" color="text-purple-600" />
        <KPICard label="Open Anomalies" value={metrics.open_anomalies} icon="⚠️" color="text-amber-600" />
        <KPICard label="Critical Flags" value={metrics.critical_anomalies} icon="🚨" color="text-red-600" />
      </div>

      {/* Health Score Row */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 mb-6">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">Overall Financial Health</h2>
        <div className="flex items-center gap-8 flex-wrap">
          <ScoreGauge score={metrics.avg_health_score} label="Overall Health" size={90} />
          <div className="flex-1 min-w-0">
            {metrics.avg_health_score !== null ? (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-2xl font-bold text-gray-800">
                    {Math.round(metrics.avg_health_score)}/100
                  </span>
                  <SeverityBadge
                    level={
                      metrics.avg_health_score >= 80 ? 'low'
                      : metrics.avg_health_score >= 60 ? 'medium'
                      : metrics.avg_health_score >= 40 ? 'high'
                      : 'critical'
                    }
                    size="md"
                  />
                </div>
                <p className="text-sm text-gray-500">
                  Average across {metrics.total_reports} completed audit{metrics.total_reports !== 1 ? 's' : ''}
                </p>
              </div>
            ) : (
              <div>
                <p className="text-gray-400 text-sm">No completed audits yet.</p>
                <Link to="/audit" className="text-blue-600 text-sm mt-1 block hover:underline">
                  Generate your first audit report →
                </Link>
              </div>
            )}
          </div>
          <div className="flex gap-8">
            <Link to="/documents" className="text-center hover:opacity-80 transition-opacity">
              <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center text-lg mb-1">📁</div>
              <span className="text-xs text-gray-500">Upload</span>
            </Link>
            <Link to="/audit" className="text-center hover:opacity-80 transition-opacity">
              <div className="w-10 h-10 bg-purple-50 rounded-lg flex items-center justify-center text-lg mb-1">🔍</div>
              <span className="text-xs text-gray-500">New Audit</span>
            </Link>
            <Link to="/chat" className="text-center hover:opacity-80 transition-opacity">
              <div className="w-10 h-10 bg-green-50 rounded-lg flex items-center justify-center text-lg mb-1">💬</div>
              <span className="text-xs text-gray-500">Ask AI</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Reports */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-700">Recent Audit Reports</h2>
            <Link to="/audit" className="text-xs text-blue-600 hover:underline">View all →</Link>
          </div>
          {metrics.recent_reports.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <p className="text-3xl mb-2">📋</p>
              <p className="text-sm">No reports yet</p>
            </div>
          ) : (
            <ul className="space-y-3">
              {metrics.recent_reports.map((report: AuditReport) => (
                <li key={report.id}>
                  <Link
                    to={`/audit/${report.id}`}
                    className="flex items-center justify-between p-3 rounded-lg hover:bg-gray-50 transition-colors group"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-800 truncate group-hover:text-blue-600">
                        {report.title}
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5">{report.period || 'No period'}</p>
                    </div>
                    <div className="ml-3 flex items-center gap-2 flex-shrink-0">
                      {report.risk_level && <SeverityBadge level={report.risk_level} />}
                      <span className={`w-2 h-2 rounded-full ${
                        report.status === 'completed' ? 'bg-green-400'
                        : report.status === 'generating' ? 'bg-blue-400 animate-pulse'
                        : 'bg-red-400'
                      }`} />
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Recent Anomalies */}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-gray-700">Open Anomalies</h2>
            <Link to="/anomalies" className="text-xs text-blue-600 hover:underline">View all →</Link>
          </div>
          {metrics.recent_anomalies.length === 0 ? (
            <div className="text-center py-8 text-gray-400">
              <p className="text-3xl mb-2">✅</p>
              <p className="text-sm">No open anomalies</p>
            </div>
          ) : (
            <ul className="space-y-3">
              {metrics.recent_anomalies.map((anomaly: Anomaly) => (
                <li key={anomaly.id}>
                  <Link
                    to="/anomalies"
                    className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors group"
                  >
                    <SeverityBadge level={anomaly.severity} />
                    <div className="min-w-0 flex-1">
                      <p className="text-sm font-medium text-gray-800 truncate group-hover:text-blue-600">
                        {anomaly.title}
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {anomaly.line_item && `${anomaly.line_item} · `}
                        {anomaly.variance_pct && `${anomaly.variance_pct > 0 ? '+' : ''}${anomaly.variance_pct.toFixed(1)}% variance`}
                      </p>
                    </div>
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}
