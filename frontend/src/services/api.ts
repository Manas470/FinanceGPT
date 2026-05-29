/**
 * FinanceGPT API Client
 * Centralized axios instance with auth interceptors
 */
import axios, { AxiosError } from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
})

// ─── Request Interceptor: attach JWT ────────────────────────
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// ─── Response Interceptor: handle auth errors ───────────────
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken && !error.config?.url?.includes('/auth/refresh')) {
        try {
          const { data } = await axios.post(
            `${BASE_URL}/auth/refresh`,
            { refresh_token: refreshToken },
            { headers: { 'Content-Type': 'application/json' } }
          )
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          if (error.config) {
            error.config.headers.Authorization = `Bearer ${data.access_token}`
            return api.request(error.config)
          }
        } catch {
          localStorage.clear()
          window.location.href = '/login'
        }
      } else {
        localStorage.clear()
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// ─── Auth ───────────────────────────────────────────────────
export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  register: (data: { email: string; full_name: string; password: string; role?: string }) =>
    api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
  changePassword: (current_password: string, new_password: string) =>
    api.post('/auth/change-password', { current_password, new_password }),
}

// ─── Documents ──────────────────────────────────────────────
export const documentsApi = {
  list: (skip = 0, limit = 50) =>
    api.get('/documents', { params: { skip, limit } }),
  get: (id: string) => api.get(`/documents/${id}`),
  upload: (formData: FormData) =>
    api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    }),
  delete: (id: string) => api.delete(`/documents/${id}`),
}

// ─── Audit ──────────────────────────────────────────────────
export const auditApi = {
  // Reports
  createReport: (data: {
    title: string
    period?: string
    source_document_ids?: string[]
    additional_context?: string
  }) => api.post('/audit/reports', data),
  listReports: (skip = 0, limit = 20) =>
    api.get('/audit/reports', { params: { skip, limit } }),
  getReport: (id: string) => api.get(`/audit/reports/${id}`),

  // Anomalies
  listAnomalies: (params?: { severity?: string; status?: string; skip?: number; limit?: number }) =>
    api.get('/audit/anomalies', { params }),
  updateAnomaly: (id: string, data: { status: string; resolution_notes?: string }) =>
    api.patch(`/audit/anomalies/${id}`, data),

  // Chat
  chat: (data: {
    message: string
    document_ids?: string[]
    conversation_history?: Array<{ role: string; content: string }>
  }) => api.post('/audit/chat', data),

  // Dashboard
  dashboard: () => api.get('/audit/dashboard'),
}

// ─── Integrations ───────────────────────────────────────────
export const integrationsApi = {
  list: () => api.get('/integrations'),
  quickbooksAuthorize: () => api.get('/integrations/quickbooks/authorize'),
  quickbooksSync: () => api.get('/integrations/quickbooks/sync'),
  xeroAuthorize: () => api.get('/integrations/xero/authorize'),
  disconnect: (id: string) => api.delete(`/integrations/${id}`),
}
