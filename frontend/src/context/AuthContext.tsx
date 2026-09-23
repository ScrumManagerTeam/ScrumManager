import { createContext, useContext, useReducer } from 'react'
import type { ReactNode } from 'react'

interface AuthState {
  token: string | null
  role: string | null
  username: string | null
  isAuthenticated: boolean
}

type AuthAction =
  | { type: 'LOGIN'; token: string; role: string; username: string }
  | { type: 'LOGOUT' }

const initialState: AuthState = {
  token: localStorage.getItem('token'),
  role: localStorage.getItem('role'),
  username: localStorage.getItem('username'),
  isAuthenticated: !!localStorage.getItem('token'),
}

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'LOGIN':
      localStorage.setItem('token', action.token)
      localStorage.setItem('role', action.role)
      localStorage.setItem('username', action.username)
      return { token: action.token, role: action.role, username: action.username, isAuthenticated: true }
    case 'LOGOUT':
      localStorage.removeItem('token')
      localStorage.removeItem('role')
      localStorage.removeItem('username')
      return { token: null, role: null, username: null, isAuthenticated: false }
    default:
      return state
  }
}

const AuthContext = createContext<{
  state: AuthState
  dispatch: React.Dispatch<AuthAction>
} | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(authReducer, initialState)
  return (
    <AuthContext.Provider value={{ state, dispatch }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}