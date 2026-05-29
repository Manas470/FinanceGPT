/** Documents upload & management page */
import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { documentsApi } from '../services/api'
import { Document, DocumentType } from '../types'
import { format } from 'date-fns'
import toast from 'react-hot-toast'

const DOC_TYPE_OPTIONS: { value: DocumentType; label: string }[] = [
  { value: 'profit_loss', label: 'P&L / Income Statement' },
  { value: 'balance_sheet', label: 'Balance Sheet' },
  { value: 'cash_flow', label: 'Cash Flow Statement' },
  { value: 'trial_balance', label: 'Trial Balance' },
  { value: 'general_ledger', label: 'General Ledger' },
  { value: 'annual_report', label: 'Annual Report' },
  { value: 'invoice', label: 'Invoices' },
  { value: 'other', label: 'Other / Auto-detect' },
]

const STATUS_STYLES: Record<string, string> = {
  pending:    'bg-gray-100 text-gray-600',
  processing: 'bg-blue-100 text-blue-700',
  processed:  'bg-green-100 text-green-700',
  failed:     'bg-red-100 text-red-700',
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function Documents() {
  const qc = useQueryClient()
  const [docType, setDocType] = useState<DocumentType>('other')
  const [periodStart, setPeriodStart] = useState('')
  const [periodEnd, setPeriodEnd] = useState('')
  const [uploading, setUploading] = useState(false)

  const { data: docs = [], isLoading } = useQuery<Document[]>({
    queryKey: ['documents'],
    queryFn: async () => { const { data } = await documentsApi.list(); return data },
    refetchInterval: 8000,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => documentsApi.delete(id),
    onSuccess: () => {
      toast.success('Document deleted')
      qc.invalidateQueries({ queryKey: ['documents'] })
    },
    onError: () => toast.error('Delete failed'),
  })

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return
    setUploading(true)
    let successCount = 0

    for (const file of acceptedFiles) {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('doc_type', docType)
      if (periodStart) fd.append('period_start', periodStart)
      if (periodEnd) fd.append('period_end', periodEnd)

      try {
        await documentsApi.upload(fd)
        successCount++
      } catch (err: any) {
        toast.error(`Failed: ${file.name} — ${err?.response?.data?.detail || 'Upload error'}`)
      }
    }

    if (successCount > 0) {
      toast.success(`${successCount} file(s) uploaded — processing in background`)
      qc.invalidateQueries({ queryKey: ['documents'] })
    }
    setUploading(false)
  }, [docType, periodStart, periodEnd, qc])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/pdf': ['.pdf'],
    },
    multiple: true,
    disabled: uploading,
  })

  return (
    <div className="flex-1 p-8 overflow-auto bg-gray-50">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Financial Documents</h1>
        <p className="text-gray-500 text-sm mt-1">Upload CSV, Excel, or PDF financial statements</p>
      </div>

      {/* Upload Zone */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 mb-6">
        <h2 className="text-sm font-semibold text-gray-700 mb-4">Upload Documents</h2>

        <div className="grid grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Document Type</label>
            <select
              value={docType}
              onChange={(e) => setDocType(e.target.value as DocumentType)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {DOC_TYPE_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Period Start</label>
            <input
              type="date"
              value={periodStart}
              onChange={(e) => setPeriodStart(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Period End</label>
            <input
              type="date"
              value={periodEnd}
              onChange={(e) => setPeriodEnd(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors
            ${isDragActive ? 'border-blue-400 bg-blue-50' : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'}
            ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
        >
          <input {...getInputProps()} />
          <div className="text-4xl mb-3">{uploading ? '⏳' : isDragActive ? '📂' : '📁'}</div>
          <p className="text-sm font-medium text-gray-700">
            {uploading ? 'Uploading...' : isDragActive ? 'Drop files here' : 'Drag & drop financial files here'}
          </p>
          <p className="text-xs text-gray-400 mt-1">
            Supports CSV, Excel (.xlsx, .xls), PDF · Max {50}MB
          </p>
          {!uploading && (
            <button className="mt-3 px-4 py-1.5 bg-blue-50 border border-blue-200 text-blue-700 text-xs rounded-lg hover:bg-blue-100 transition-colors">
              Browse files
            </button>
          )}
        </div>
      </div>

      {/* Documents List */}
      {isLoading ? (
        <div className="text-center py-12 text-gray-400">Loading...</div>
      ) : docs.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-5xl mb-3">📂</p>
          <p className="font-medium text-gray-600">No documents uploaded yet</p>
          <p className="text-sm mt-1">Upload your financial statements above to get started</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">File</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Type</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Status</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Period</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Size</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">Uploaded</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {docs.map((doc: Document) => (
                <tr key={doc.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-5 py-3">
                    <div className="flex items-center gap-2">
                      <span>{doc.mime_type.includes('pdf') ? '📄' : doc.mime_type.includes('csv') ? '📊' : '📗'}</span>
                      <span className="font-medium text-gray-800 truncate max-w-xs">{doc.original_filename}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-gray-500 capitalize">{doc.doc_type.replace(/_/g, ' ')}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[doc.status]}`}>
                      {doc.status === 'processing' && '⏳ '}
                      {doc.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {doc.period_start && doc.period_end
                      ? `${doc.period_start} → ${doc.period_end}`
                      : doc.period_start || '—'}
                  </td>
                  <td className="px-4 py-3 text-gray-500">{formatFileSize(doc.file_size)}</td>
                  <td className="px-4 py-3 text-gray-500 text-xs">
                    {format(new Date(doc.created_at), 'MMM d, yyyy')}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => {
                        if (confirm(`Delete ${doc.original_filename}?`))
                          deleteMutation.mutate(doc.id)
                      }}
                      className="text-red-400 hover:text-red-600 text-xs"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
