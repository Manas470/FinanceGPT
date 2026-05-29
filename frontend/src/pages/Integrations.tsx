/** Integrations page — QuickBooks & Xero */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { integrationsApi } from '../services/api'
import { Integration } from '../types'
import { format } from 'date-fns'
import toast from 'react-hot-toast'

const PROVIDER_META: Record<string, { name: string; icon: string; color: string; desc: string }> = {
  quickbooks: {
    name: 'QuickBooks Online',
    icon: '🟩',
    color: 'border-green-200 bg-green-50',
    desc: 'Sync P&L, Balance Sheet, and cash flow directly from QuickBooks',
  },
  xero: {
    name: 'Xero',
    icon: '🔵',
    color: 'border-blue-200 bg-blue-50',
    desc: 'Connect Xero accounting data for real-time financial analysis',
  },
}

export default function Integrations() {
  const qc = useQueryClient()

  const { data: integrations = [] } = useQuery<Integration[]>({
    queryKey: ['integrations'],
    queryFn: async () => { const { data } = await integrationsApi.list(); return data },
  })

  const connectQB = useMutation({
    mutationFn: async () => {
      const { data } = await integrationsApi.quickbooksAuthorize()
      window.location.href = data.auth_url
    },
    onError: () => toast.error('Failed to initiate QuickBooks connection'),
  })

  const connectXero = useMutation({
    mutationFn: async () => {
      const { data } = await integrationsApi.xeroAuthorize()
      window.location.href = data.auth_url
    },
    onError: () => toast.error('Failed to initiate Xero connection'),
  })

  const syncQB = useMutation({
    mutationFn: integrationsApi.quickbooksSync,
    onSuccess: () => { toast.success('QuickBooks sync complete!'); qc.invalidateQueries({ queryKey: ['integrations'] }) },
    onError: () => toast.error('Sync failed'),
  })

  const disconnect = useMutation({
    mutationFn: (id: string) => integrationsApi.disconnect(id),
    onSuccess: () => { toast.success('Integration disconnected'); qc.invalidateQueries({ queryKey: ['integrations'] }) },
    onError: () => toast.error('Disconnect failed'),
  })

  const connectedProviders = integrations.filter((i: Integration) => i.is_active).map((i: Integration) => i.provider)

  return (
    <div className="flex-1 p-8 overflow-auto bg-gray-50">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Integrations</h1>
        <p className="text-gray-500 text-sm mt-1">Connect your accounting software for real-time data sync</p>
      </div>

      {/* Available Integrations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-8">
        {/* QuickBooks */}
        <div className={`bg-white rounded-xl border p-6 ${connectedProviders.includes('quickbooks') ? 'border-green-200' : 'border-gray-100 shadow-sm'}`}>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-green-50 rounded-xl flex items-center justify-center text-2xl">🟩</div>
              <div>
                <h3 className="font-semibold text-gray-800">QuickBooks Online</h3>
                <p className="text-xs text-gray-500">Intuit QuickBooks</p>
              </div>
            </div>
            {connectedProviders.includes('quickbooks') ? (
              <span className="bg-green-100 text-green-700 text-xs px-2 py-1 rounded-full font-medium">Connected</span>
            ) : (
              <span className="bg-gray-100 text-gray-500 text-xs px-2 py-1 rounded-full">Not connected</span>
            )}
          </div>

          <p className="text-sm text-gray-600 mt-3">
            Sync P&L, Balance Sheet, and cash flow statements directly from QuickBooks Online.
          </p>

          <div className="mt-4 flex gap-2">
            {connectedProviders.includes('quickbooks') ? (
              <>
                <button
                  onClick={() => syncQB.mutate()}
                  disabled={syncQB.isPending}
                  className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-300 text-white text-sm font-medium py-2 rounded-lg transition-colors"
                >
                  {syncQB.isPending ? 'Syncing...' : '↻ Sync Now'}
                </button>
                {integrations.find((i: Integration) => i.provider === 'quickbooks') && (
                  <button
                    onClick={() => disconnect.mutate(integrations.find((i: Integration) => i.provider === 'quickbooks')!.id)}
                    className="px-3 py-2 border border-gray-200 text-gray-600 text-sm rounded-lg hover:bg-gray-50"
                  >
                    Disconnect
                  </button>
                )}
              </>
            ) : (
              <button
                onClick={() => connectQB.mutate()}
                disabled={connectQB.isPending}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white text-sm font-medium py-2 rounded-lg transition-colors"
              >
                Connect QuickBooks
              </button>
            )}
          </div>
        </div>

        {/* Xero */}
        <div className={`bg-white rounded-xl border p-6 ${connectedProviders.includes('xero') ? 'border-blue-200' : 'border-gray-100 shadow-sm'}`}>
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center text-2xl">🔵</div>
              <div>
                <h3 className="font-semibold text-gray-800">Xero</h3>
                <p className="text-xs text-gray-500">Xero Accounting</p>
              </div>
            </div>
            {connectedProviders.includes('xero') ? (
              <span className="bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded-full font-medium">Connected</span>
            ) : (
              <span className="bg-gray-100 text-gray-500 text-xs px-2 py-1 rounded-full">Not connected</span>
            )}
          </div>

          <p className="text-sm text-gray-600 mt-3">
            Connect Xero to automatically pull financial reports, invoices, and reconciliation data.
          </p>

          <div className="mt-4">
            {connectedProviders.includes('xero') ? (
              <div className="flex gap-2">
                <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-2 rounded-lg">
                  ↻ Sync Now
                </button>
                {integrations.find((i: Integration) => i.provider === 'xero') && (
                  <button
                    onClick={() => disconnect.mutate(integrations.find((i: Integration) => i.provider === 'xero')!.id)}
                    className="px-3 py-2 border border-gray-200 text-gray-600 text-sm rounded-lg hover:bg-gray-50"
                  >
                    Disconnect
                  </button>
                )}
              </div>
            ) : (
              <button
                onClick={() => connectXero.mutate()}
                disabled={connectXero.isPending}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-2 rounded-lg transition-colors"
              >
                Connect Xero
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Connected integrations table */}
      {integrations.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-50">
            <h2 className="text-sm font-semibold text-gray-700">Connection History</h2>
          </div>
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase">Provider</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Status</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Company</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-gray-500 uppercase">Last Synced</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {integrations.map((i: Integration) => (
                <tr key={i.id} className="hover:bg-gray-50">
                  <td className="px-5 py-3 font-medium text-gray-800 capitalize">{i.provider}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                      i.status === 'active' ? 'bg-green-100 text-green-700'
                      : i.status === 'expired' ? 'bg-amber-100 text-amber-700'
                      : 'bg-red-100 text-red-700'
                    }`}>
                      {i.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500">{i.external_company_name || '—'}</td>
                  <td className="px-4 py-3 text-gray-500">
                    {i.last_synced_at ? format(new Date(i.last_synced_at), 'MMM d, yyyy HH:mm') : 'Never'}
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
