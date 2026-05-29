/** Main navigation sidebar */
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../hooks/useAuth'

const NAV = [
  { to: '/dashboard', icon: '📊', label: 'Dashboard' },
  { to: '/documents', icon: '📁', label: 'Documents' },
  { to: '/audit', icon: '🔍', label: 'Audit Reports' },
  { to: '/anomalies', icon: '⚠️', label: 'Anomalies' },
  { to: '/chat', icon: '💬', label: 'Financial Q&A' },
  { to: '/integrations', icon: '🔗', label: 'Integrations' },
]

export function Sidebar() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col min-h-screen">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <span className="text-2xl">💰</span>
          <div>
            <h1 className="text-lg font-bold text-white">FinanceGPT</h1>
            <p className="text-xs text-gray-400">CFO Audit Platform</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {NAV.map(({ to, icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
              ${isActive
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:bg-gray-800 hover:text-white'
              }`
            }
          >
            <span>{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>

      {/* User */}
      <div className="px-4 py-4 border-t border-gray-700">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-sm font-bold">
            {user?.full_name?.[0]?.toUpperCase() || '?'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">{user?.full_name}</p>
            <p className="text-xs text-gray-400 truncate">{user?.role}</p>
          </div>
        </div>
        <button
          onClick={handleLogout}
          className="w-full text-left text-xs text-gray-400 hover:text-white transition-colors px-1 py-1"
        >
          → Sign out
        </button>
      </div>
    </aside>
  )
}
