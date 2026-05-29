/** FinanceGPT App — root routing */
import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { useEffect } from 'react'
import { useAuthStore } from './hooks/useAuth'
import { Sidebar } from './components/layout/Sidebar'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import Documents from './pages/Documents'
import AuditReports from './pages/AuditReports'
import Anomalies from './pages/Anomalies'
import Chat from './pages/Chat'
import Integrations from './pages/Integrations'

const qc = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30000 },
  },
})

function AppLayout() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 flex flex-col overflow-hidden">
        <Outlet />
      </main>
    </div>
  )
}

function RequireAuth() {
  const { isAuthenticated, isLoading, fetchMe } = useAuthStore()

  useEffect(() => {
    if (isAuthenticated) fetchMe()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated])

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin text-4xl mb-3">⚙️</div>
          <p className="text-gray-500 text-sm">Loading FinanceGPT...</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <AppLayout />
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route element={<RequireAuth />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/documents" element={<Documents />} />
            <Route path="/audit" element={<AuditReports />} />
            <Route path="/audit/:id" element={<AuditReports />} />
            <Route path="/anomalies" element={<Anomalies />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/integrations" element={<Integrations />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: { fontSize: '14px', borderRadius: '8px' },
        }}
      />
    </QueryClientProvider>
  )
}
