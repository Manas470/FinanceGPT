/** Zustand auth store */
import { create } from 'zustand'
import { User } from '../types'
import { authApi } from '../services/api'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  fetchMe: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem('access_token'),
  isLoading: false,

  login: async (email, password) => {
    set({ isLoading: true })
    try {
      const { data } = await authApi.login(email, password)
      localStorage.setItem('access_token', data.access_token)
      localStorage.setItem('refresh_token', data.refresh_token)
      const { data: user } = await authApi.me()
      set({ user, isAuthenticated: true, isLoading: false })
    } catch (err) {
      set({ isLoading: false })
      throw err  // re-throw so the Login page can show the error toast
    }
  },

  logout: () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    set({ user: null, isAuthenticated: false })
  },

  fetchMe: async () => {
    try {
      const { data } = await authApi.me()
      set({ user: data, isAuthenticated: true })
    } catch {
      set({ user: null, isAuthenticated: false })
    }
  },
}))
