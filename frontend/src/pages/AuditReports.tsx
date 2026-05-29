/** Audit Reports page — list and generate CFO reports */
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { auditApi, documentsApi } from '../services/api'
import { AuditReport, Document } from '../types'
import { SeverityBadge } from '../components/ui/SeverityBadge'
import { ScoreGauge } from '../components/ui/ScoreGauge'
import { format } from 'date-fns'
import toast from 'react-hot-toast'

function ReportCard({ report }: { report: AuditReport }) {
  const statusIcon = {
    generating: '⏳',
    completed: '✅',
    failed: '❌',
  }[report.status]

  return (
    <Link
      to={`/audit/${report.id}`}
      className="block bg-white rounded-xl border border-gray-100 shadow-sm p-5 hover:shadow-md hover:border-blue-100 transition-all group"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span>{statusIcon}</span>
            <h3 className="font-semibold text-gray-800 group-hover:text-blue-600 truncate">
              {report.title}
            </h3>
          </div>
          <p className="text-sm text-gray-500 mt-1">{report.period || 'No period specified'}</p>
          {report.executive_summary && (
            <p className="text-xs text-gray-400 mt-2 line-clamp-2">{report.executive_summary}</p>
          )}
        </div>
        <div className="flex flex-col items-center gap-1 flex-shrink-0">
          {report.overall_health_score !== null && (
            <ScoreGauge score={report.overall_health_score} label="Health" size={60} />
          )}
          {report.risk_level && <SeverityBadge level={report.risk_level} />}
        </div>
      </div>

      {report.status === 'completed' && (
        <div className="mt-4 grid grid-cols-4 gap-2 pt-3 border-t border-gray-50">
          {[
            ['Liquidity', report.liquidity_score],
            ['Profitability', report.profitability_score],
            ['Solvency', report.solvency_score],
            ['Efficiency', report.efficiency_score],
          ].map(([label, score]) => (
            <div key={label as string} className="text-center">
              <p className="text-xs text-gray-400">{label}</p>
              <p className="text-sm font-bold text-gray-700">
                {score !== null ? `${Math.round(score as number)}` : '—'}
              </p>
            </div>
          ))}
        </div>
      )}

      <p className="text-xs text-gray-300 mt-3">
        {format(new Date(report.created_at), 'MMM d, yyyy HH:mm')}
      </p>
    </Link>
  )
}

export default function AuditReports() {
  const qc = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [title, setTitle] = useState('')
  const [period, setPeriod] = useState('')
  const [context, setContext] = useState('')
  const [selectedDocs, setSelectedDocs] = useState<string[]>([])

  const { data: reports = [], isLoading } = useQuery<AuditReport[]>({
    queryKey: ['audit-reports'],
    queryFn: async () => { const { data } = await auditApi.listReports(); return data },
    refetchInterval: 15000,
  })

  const { data: docs = [] } = useQuery<Document[]>({
    queryKey: ['documents'],
    queryFn: async () => { const { data } = await documentsApi.list(); return data },
  })

  const createMutation = useMutation({
    mutationFn: () => auditApi.createReport({
      title,
      period: period || undefined,
      source_document_ids: selectedDocs,
      additional_context: context,
    }),
    onSuccess: () => {
      toast.success('Audit report generation started!')
      setShowForm(false)
      setTitle(''); setPeriod(''); setContext(''); setSelectedDocs([])
      qc.invalidateQueries({ queryKey: ['audit-reports'] })
    },
    onError: (err: any) => toast.error(err?.response?.data?.detail || 'Failed to create report'),
  })

  const processedDocs = docs.filter((d: Document) => d.status === 'processed')

  return (
    <div className="flex-1 p-8 overflow-auto bg-gray-50">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Audit Reports</h1>
          <p className="text-gray-500 text-sm mt-1">AI-generated CFO-grade financial audits</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-2 rounded-lg text-sm transition-colors flex items-center gap-2"
        >
          <span>+</span> New Audit Report
        </button>
      </div>

      {/* Create Report Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-lg">
            <h2 className="text-lg font-semibold text-gray-800 mb-4">Generate CFO Audit Report</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Report Title *</label>
                <input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Q3 2024 Financial Audit"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Period</label>
                <input
                  value={period}
                  onChange={(e) => setPeriod(e.target.value)}
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Q3 2024 / FY 2023"
                />
              </div>
              {processedDocs.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Source Documents (optional — uses all if none selected)
                  </label>
                  <div className="border rounded-lg max-h-36 overflow-y-auto p-2 space-y-1">
                    {processedDocs.map((doc: Document) => (
                      <label key={doc.id} className="flex items-center gap-2 p-1 hover:bg-gray-50 rounded cursor-pointer">
                        <input
                          type="checkbox"
                          checked={selectedDocs.includes(doc.id)}
                          onChange={(e) => {
                            if (e.target.checked) setSelectedDocs([...selectedDocs, doc.id])
                            else setSelectedDocs(selectedDocs.filter((id) => id !== doc.id))
                          }}
                        />
                        <span className="text-xs text-gray-700 truncate">{doc.original_filename}</span>
                        <span className="text-xs text-gray-400 ml-auto">{doc.doc_type}</span>
                      </label>
                    ))}
                  </div>
                </div>
              )}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Additional Context</label>
                <textarea
                  value={context}
                  onChange={(e) => setContext(e.target.value)}
                  rows={3}
                  className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                  placeholder="Industry context, specific concerns, benchmarks to use..."
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => createMutation.mutate()}
                  disabled={!title || createMutation.isPending}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white font-semibold py-2 rounded-lg text-sm transition-colors"
                >
                  {createMutation.isPending ? '⏳ Generating...' : '🔍 Generate Report'}
                </button>
                <button
                  onClick={() => setShowForm(false)}
                  className="px-4 py-2 border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Reports List */}
      {isLoading ? (
        <div className="text-center py-16 text-gray-400">
          <div className="animate-spin text-3xl mb-3">⚙️</div>
          <p>Loading reports...</p>
        </div>
      ) : reports.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-5xl mb-4">📊</p>
          <h3 className="text-lg font-medium text-gray-700">No audit reports yet</h3>
          <p className="text-gray-400 text-sm mt-1 mb-4">Upload financial documents and generate your first CFO audit</p>
          <button
            onClick={() => setShowForm(true)}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg text-sm font-medium"
          >
            Generate First Report
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {reports.map((report: AuditReport) => (
            <ReportCard key={report.id} report={report} />
          ))}
        </div>
      )}
    </div>
  )
}
