import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const { state, dispatch } = useAuth()

  const nav = [
    { path: '/dashboard', label: 'Dashboard', icon: (
      <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
        <rect x="1" y="1" width="6" height="6" rx="1.5"/><rect x="9" y="1" width="6" height="6" rx="1.5"/>
        <rect x="1" y="9" width="6" height="6" rx="1.5"/><rect x="9" y="9" width="6" height="6" rx="1.5"/>
      </svg>
    )},
    { path: '/backlog', label: 'Backlog', icon: (
      <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M2 4h12M2 8h8M2 12h10"/>
      </svg>
    )},
    { path: '/sprint', label: 'Sprints', icon: (
      <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
        <circle cx="8" cy="8" r="6"/><path d="M8 5v3l2 2"/>
      </svg>
    )},
    { path: '/tasks', label: 'Tasks', icon: (
      <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M4 4h8M4 8h5M4 12h6"/><path d="M13 10l-2 2-1-1"/>
      </svg>
    )},
    { path: '/reports', label: 'Reports', icon: (
      <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M2 12 L5 7 L8 9 L11 4 L14 6"/><path d="M2 14h12"/>
      </svg>
    )},
  ]

  const initials = state.username
    ? state.username.slice(0, 2).toUpperCase()
    : '?'

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: '#0d0f14', fontFamily: 'Inter, system-ui, sans-serif' }}>
      {/* Topbar */}
      <div style={{ background: '#0d0f14', borderBottom: '0.5px solid rgba(255,255,255,0.07)', padding: '0 20px', height: '48px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#f1f5f9', fontSize: '14px', fontWeight: 500 }}>
          <div style={{ width: '22px', height: '22px', borderRadius: '6px', background: '#6366f1', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <svg width="12" height="12" viewBox="0 0 12 12" fill="white">
              <path d="M2 2h3v3H2zM7 2h3v3H7zM2 7h3v3H2zM7 7h3v3H7z"/>
            </svg>
          </div>
          ScrumManager
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{ background: 'rgba(99,102,241,0.15)', color: '#a5b4fc', fontSize: '11px', padding: '4px 10px', borderRadius: '20px', border: '0.5px solid rgba(99,102,241,0.3)' }}>
            {state.role}
          </div>
          <div style={{ width: '26px', height: '26px', borderRadius: '50%', background: 'linear-gradient(135deg,#6366f1,#8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: '10px', fontWeight: 600 }}>
            {initials}
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Sidebar */}
        <div style={{ width: '200px', background: '#0a0c11', borderRight: '0.5px solid rgba(255,255,255,0.06)', padding: '16px 10px', display: 'flex', flexDirection: 'column', gap: '2px', flexShrink: 0 }}>
          <div style={{ fontSize: '10px', color: '#374151', textTransform: 'uppercase', letterSpacing: '0.08em', padding: '8px 10px 4px' }}>Menu</div>
          {nav.map(item => {
            const active = location.pathname === item.path
            return (
              <div
                key={item.path}
                onClick={() => navigate(item.path)}
                style={{
                  display: 'flex', alignItems: 'center', gap: '10px',
                  padding: '8px 10px', borderRadius: '8px', cursor: 'pointer',
                  color: active ? '#a5b4fc' : '#4b5563',
                  background: active ? 'rgba(99,102,241,0.15)' : 'transparent',
                  fontSize: '13px', transition: 'all 0.15s',
                }}
                onMouseEnter={e => { if (!active) { (e.currentTarget as HTMLDivElement).style.color = '#94a3b8'; (e.currentTarget as HTMLDivElement).style.background = 'rgba(255,255,255,0.04)' }}}
                onMouseLeave={e => { if (!active) { (e.currentTarget as HTMLDivElement).style.color = '#4b5563'; (e.currentTarget as HTMLDivElement).style.background = 'transparent' }}}
              >
                {item.icon}
                {item.label}
              </div>
            )
          })}
          <div style={{ marginTop: 'auto', paddingTop: '16px', borderTop: '0.5px solid rgba(255,255,255,0.06)' }}>
            <div
              onClick={() => { dispatch({ type: 'LOGOUT' }); navigate('/login') }}
              style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 10px', borderRadius: '8px', cursor: 'pointer', color: '#4b5563', fontSize: '13px', transition: 'all 0.15s' }}
              onMouseEnter={e => { (e.currentTarget as HTMLDivElement).style.color = '#f87171'; (e.currentTarget as HTMLDivElement).style.background = 'rgba(239,68,68,0.08)' }}
              onMouseLeave={e => { (e.currentTarget as HTMLDivElement).style.color = '#4b5563'; (e.currentTarget as HTMLDivElement).style.background = 'transparent' }}
            >
              <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M6 2H3a1 1 0 00-1 1v10a1 1 0 001 1h3M10 11l3-3-3-3M13 8H6"/>
              </svg>
              Logout
            </div>
          </div>
        </div>

        {/* Page content */}
        <div style={{ flex: 1, overflowY: 'auto', background: '#0d0f14' }}>
          {children}
        </div>
      </div>
    </div>
  )
}
