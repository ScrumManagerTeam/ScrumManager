import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { isAxiosError } from 'axios'
import { useAuth } from '../context/AuthContext'
import Layout from '../components/Layout'
import api from '../api/client'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts'

interface Sprint {
  id: number
  status: string
  capacity: number
}

interface BurndownData {
  days: string[]
  ideal: number[]
  actual: number[]
}

interface VelocityEntry {
  sprint_id: number
  sprint_label: string
  effort_completed: number
}

export default function Reports() {
  const [sprints, setSprints] = useState<Sprint[]>([])
  const [selectedSprint, setSelectedSprint] = useState<number | null>(null)
  const [burndown, setBurndown] = useState<BurndownData | null>(null)
  const [velocity, setVelocity] = useState<VelocityEntry[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { state, dispatch } = useAuth()
  const navigate = useNavigate()

  const handleAuthError = (err: unknown) => {
    const status = isAxiosError(err) ? err.response?.status : undefined
    if (status === 401 || status === 422) {
      dispatch({ type: 'LOGOUT' })
      navigate('/login')
      return true
    }
    return false
  }

  useEffect(() => {
    if (!state.isAuthenticated) { navigate('/login'); return }
    Promise.all([
      api.get('/sprints/?per_page=100'),
      api.get('/velocity/sprints/velocity'),
    ]).then(([sprintRes, velocityRes]) => {
      setSprints(sprintRes.data.sprints)
      setVelocity(velocityRes.data)
    }).catch(err => {
      if (!handleAuthError(err)) setError('Failed to load sprints')
    })
  }, [])

  const selectSprint = (id: number | null) => {
    setSelectedSprint(id)
    setBurndown(null)
    setError('')
    setLoading(id !== null)
  }

  useEffect(() => {
    if (!selectedSprint) return
    // Ignore a slow response if the user has already picked another sprint
    let stale = false
    api.get(`/burndown/sprints/${selectedSprint}/burndown`)
      .then(res => { if (!stale) setBurndown(res.data) })
      .catch(err => {
        if (!stale && !handleAuthError(err)) setError('Failed to load burndown chart')
      })
      .finally(() => { if (!stale) setLoading(false) })
    return () => { stale = true }
  }, [selectedSprint])

  const chartData = burndown
    ? burndown.days.map((day, i) => ({
        day,
        Ideal: burndown.ideal[i],
        Actual: burndown.actual[i],
      }))
    : []

  return (
    <Layout>
      <div style={{ padding: '32px' }}>
        <h1 style={{ color: '#f1f5f9', marginBottom: '8px' }}>Reports</h1>
        <p style={{ color: '#94a3b8', marginBottom: '32px' }}>
          Sprint burndown and velocity
        </p>

        {/* Sprint selector */}
        <div style={{ marginBottom: '32px' }}>
          <label style={{ color: '#94a3b8', display: 'block', marginBottom: '8px' }}>
            Select a sprint
          </label>
          <select
            value={selectedSprint ?? ''}
            onChange={e => selectSprint(e.target.value ? Number(e.target.value) : null)}
            style={{
              background: '#131720',
              color: '#f1f5f9',
              border: '1px solid rgba(255,255,255,0.06)',
              borderRadius: '8px',
              padding: '8px 16px',
              fontSize: '14px',
            }}
          >
            <option value="">-- Pick a sprint --</option>
            {sprints.map(s => (
              <option key={s.id} value={s.id}>
                Sprint #{s.id} — {s.status}
              </option>
            ))}
          </select>
        </div>

        {/* Burndown chart */}
        {error && (
          <div style={{ background: 'rgba(239,68,68,0.1)', border: '0.5px solid rgba(239,68,68,0.3)', color: '#fca5a5', padding: '10px 14px', borderRadius: '8px', fontSize: '13px', marginBottom: '32px' }}>
            {error}
          </div>
        )}
        {loading && <p style={{ color: '#94a3b8' }}>Loading chart...</p>}
        {burndown && !loading && burndown.days.length === 0 && (
          <p style={{ color: '#94a3b8', marginBottom: '32px' }}>
            Sprint #{selectedSprint} hasn't started yet, so there is nothing to chart.
          </p>
        )}
        {burndown && !loading && burndown.days.length > 0 && (
          <div style={{
            background: '#131720',
            borderRadius: '12px',
            padding: '24px',
            marginBottom: '32px',
            border: '1px solid rgba(255,255,255,0.06)'
          }}>
            <h2 style={{ color: '#f1f5f9', marginBottom: '24px', fontSize: '16px' }}>
              Burndown chart — Sprint #{selectedSprint}
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="day" stroke="#94a3b8" tick={{ fontSize: 12 }} />
                <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    background: '#0d0f14',
                    border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: '8px',
                    color: '#f1f5f9'
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="Ideal"
                  stroke="#6366f1"
                  strokeDasharray="5 5"
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="Actual"
                  stroke="#22c55e"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Velocity table */}
        {velocity.length > 0 && (
          <div style={{
            background: '#131720',
            borderRadius: '12px',
            padding: '24px',
            border: '1px solid rgba(255,255,255,0.06)'
          }}>
            <h2 style={{ color: '#f1f5f9', marginBottom: '16px', fontSize: '16px' }}>
              Velocity — completed sprints
            </h2>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                  <th style={{ color: '#94a3b8', textAlign: 'left', padding: '8px', fontSize: '12px' }}>Sprint</th>
                  <th style={{ color: '#94a3b8', textAlign: 'left', padding: '8px', fontSize: '12px' }}>Effort completed (h)</th>
                </tr>
              </thead>
              <tbody>
                {velocity.map(v => (
                  <tr key={v.sprint_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                    <td style={{ color: '#f1f5f9', padding: '8px', fontSize: '14px' }}>{v.sprint_label}</td>
                    <td style={{ color: '#22c55e', padding: '8px', fontSize: '14px' }}>{v.effort_completed}h</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {velocity.length === 0 && !error && (
          <p style={{ color: '#94a3b8' }}>No completed sprints yet — velocity appears once a sprint is completed.</p>
        )}
      </div>
    </Layout>
  )
}