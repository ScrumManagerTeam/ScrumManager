import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import Login from './pages/Login'
import Backlog from './pages/Backlog'
import SprintPage from './pages/Sprint'
import TasksPage from './pages/Tasks'
import Dashboard from './pages/Dashboard'
import ReportsPage from './pages/Reports'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/backlog" element={<Backlog />} />
          <Route path="/sprint" element={<SprintPage />} />
          <Route path="/tasks" element={<TasksPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="*" element={<Navigate to="/dashboard" />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App