/** Anomaly Management page */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { auditApi } from '../services/api'
import { Anomaly, Severity } from '../types'
import { SeverityBadge } from '../components/ui/SeverityBadge'
import { format } from 'date-fns'
import toast from 'react-hot-toast'

const ANOMALY_TYPE_LABELS: Record<string, string> = {
  unusual_variance: 'Unusual Variance',
  missing_data: 'Missing Data',
  ratio_outlier: 'Ratio Outlier',
  trend_reversal: 'Trend Reversal',
  duplicate_entry: 'Duplicate Entry',
  round_number: "Round Number (Benford's)",
  year_end_spike: 'Year-End Spike',
  intercompany: 'Intercompany',
  unreconciled: 'Unreconciled',
  policy_breach: 'Policy Breach',
}

export default function Anomalies() {
  const qc = useQueryClient()
  const [filterSeverity, setFilterSeverity] = useState('')
  const [filterStatus, setFilterStatus] = useState('open')
  const [selected, setSelected] = useState<Anomaly | null>(null)

  const { data: anomalies = [], isLoading } = useQuery<Anomaly[]>({
    queryKey: ['anomalies', filterSeverity, filterStatus],
    queryFn: async () => {
      const { data } = await auditApi.listAnomalies({
        severity: filterSeverity || undefined,
        status: filterStatus || undefined,
        limit: 100,
      })
      return data
    },
    refetchInterval: 30000,
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, status, notes }: { id: string; status: string; notes?: string }) =>
      auditApi.updateAnomaly(id, { status, resolution_notes: notes }),
    onSuccess: () => {
      toast.success('Anomaly updated')
      setSelected(null)
      qc.invalidateQueries({ queryKey: ['anomalies'] })
      qc.invalidateQueries({ queryKey: ['dashboard'] })
    },
    onError: () => toast.error('Update failed'),
  })

  const severityCount = (s: Severity) => anomalies.filter((a: Anomaly) => a.severity === s).length

  return (
    <div className="flex-1 flex overflow-hidden bg-gray-50">
      {/* List */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="bg-white border-b border-gray-100 px-8 py-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Anomalies</h1>
              <p className="text-sm text-gray-500 mt-0.5">AI-detected financial irregularities requiring review</p>
            </div>
            <div className="flex items-center gap-2 text-xs">
              {(['critical', 'high', 'medium', 'low'] as Severity[]).map((s) => (
                <span key={s} className="flex items-center gap-1">
                  <SeverityBadge level={s} />
                  <span className="text-gray-500">{severityCount(s)}</span>
                </span>
              ))}
            </div>
          </div>

          {/* Filters */}
          <div className="flex gap-3">
            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
              className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Statuses</option>
              <option value="open">Open</option>
              <option value="under_review">Under Review</option>
              <option value="resolved">Resolved</option>
              <option value="false_positive">False Positive</option>
            </select>
          </div>
        </div>

        <div className="flex-1 overflow-auto px-8 py-4">
          {isLoading ? (
            <div className="text-center py-12 text-gray-400">Loading anomalies...</div>
          ) : anomalies.length === 0 ? (
            <div className="text-center py-16 text-gray-400">
              <p className="text-5xl mb-3">✅</p>
              <p className="font-medium text-gray-600">No anomalies found</p>
              <p className="text-sm mt-1">Generate an audit report to detect financial irregularities</p>
            </div>
          ) : (
            <div className="space-y-2">
              {anomalies.map((anomaly: Anomaly) => (
                <button
                  key={anomaly.id}
                  onClick={() => setSelected(anomaly)}
                  className={`w-full text-left bg-white rounded-xl border p-4 hover:shadow-sm transition-all ${
                    selected?.id === anomaly.id ? 'border-blue-400 shadow-sm' : 'border-gray-100'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <SeverityBadge level={anomaly.severity} size="md" />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-semibold text-gray-800 text-sm">{anomaly.title}</span>
                        <span className="text-xs text-gray-400 bg-gray-50 px-2 py-0.5 rounded-full">
                          {ANOMALY_TYPE_LABELS[anomaly.anomaly_type] || anomaly.anomaly_type}
                        </span>
                      </div>
                      {anomaly.line_item && (
                        <p className="text-xs text-gray-500 mt-0.5">
                          Line: <span className="font-medium">{anomaly.line_item}</span>
                          {anomaly.amount && ` · ${anomaly.amount.toLocaleString()}`}
                          {anomaly.variance_pct && ` · ${anomaly.variance_pct > 0 ? '+' : ''}${anomaly.variance_pct.toFixed(1)}% variance`}
                        </p>
                      )}
                      <p className="text-xs text-gray-400 mt-1 line-clamp-1">{anomaly.description}</p>
                    </div>
                    <div className="flex-shrink-0 text-right">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${
                        anomaly.status === 'open' ? 'bg-amber-50 text-amber-700'
                        : anomaly.status === 'resolved' ? 'bg-green-50 text-green-700'
                        : 'bg-gray-50 text-gray-500'
                      }`}>
                        {anomaly.status.replace(/_/g, ' ')}
                      </span>
                      <p className="text-xs text-gray-300 mt-1">
                        {format(new Date(anomaly.created_at), 'MMM d')}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Detail Panel */}
      {selected && (
        <div className="w-96 bg-white border-l border-gray-100 overflow-auto flex flex-col">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="font-semibold text-gray-800 text-sm">Anomaly Detail</h2>
            <button onClick={() => setSelected(null)} className="text-gray-400 hover:text-gray-600">✕</button>
          </div>

          <div className="flex-1 overflow-auto px-5 py-4 space-y-5">
            <div>
              <SeverityBadge level={selected.severity} size="md" />
              <h3 className="text-lg font-bold text-gray-900 mt-2">{selected.title}</h3>
              <p className="text-xs text-gray-400 mt-1">
                {ANOMALY_TYPE_LABELS[selected.anomaly_type]} · Confidence: {
                  selected.confidence_score ? `${(selected.confidence_score * 100).toFixed(0)}%` : 'N/A'
                }
              </p>
            </div>

            {selected.line_item && (
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500 mb-1">Line Item</p>
                <p className="font-semibold text-gray-800">{selected.line_item}</p>
                {selected.amount && (
                  <div className="grid grid-cols-2 gap-2 mt-2">
                    <div>
                      <p className="text-xs text-gray-400">Actual</p>
                      <p className="font-bold text-gray-800">${selected.amount.toLocaleString()}</p>
                    </div>
                    {selected.expected_amount && (
                      <div>
                        <p className="text-xs text-gray-400">Expected</p>
                        <p className="font-bold text-gray-600">${selected.expected_amount.toLocaleString()}</p>
                      </div>
                    )}
                    {selected.variance_pct && (
                      <div className="col-span-2">
                        <p className="text-xs text-gray-400">Variance</p>
                        <p className={`font-bold ${Math.abs(selected.variance_pct) > 20 ? 'text-red-600' : 'text-amber-600'}`}>
                          {selected.variance_pct > 0 ? '+' : ''}{selected.variance_pct.toFixed(1)}%
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Description</p>
              <p className="text-sm text-gray-700">{selected.description}</p>
            </div>

            {selected.ai_explanation && (
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase mb-1">AI Analysis</p>
                <p className="text-sm text-gray-700 bg-blue-50 p-3 rounded-lg">{selected.ai_explanation}</p>
              </div>
            )}

            {selected.recommendation && (
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase mb-1">Recommendation</p>
                <p className="text-sm text-gray-700">{selected.recommendation}</p>
              </div>
            )}
          </div>

          {selected.status === 'open' && (
            <div className="px-5 py-4 border-t border-gray-100 space-y-2">
              <p className="text-xs font-semibold text-gray-500 mb-2">Update Status</p>
              <button
                onClick={() => updateMutation.mutate({ id: selected.id, status: 'under_review' })}
                className="w-full py-2 border border-blue-200 text-blue-700 rounded-lg text-sm hover:bg-blue-50 transition-colors"
              >
                Mark Under Review
              </button>
              <button
                onClick={() => updateMutation.mutate({ id: selected.id, status: 'resolved' })}
                className="w-full py-2 bg-green-600 text-white rounded-lg text-sm hover:bg-green-700 transition-colors"
              >
                Mark Resolved
              </button>
              <button
                onClick={() => updateMutation.mutate({ id: selected.id, status: 'false_positive' })}
                className="w-full py-2 border border-gray-200 text-gray-600 rounded-lg text-sm hover:bg-gray-50 transition-colors"
              >
                Mark False Positive
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
