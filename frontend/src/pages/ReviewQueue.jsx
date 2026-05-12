import { useState, useEffect } from 'react'
import ReminderCard from '../components/ReminderCard'

const APPT_TYPES = [
  'Surgery Consultation','Mental Health Session','Cancer Treatment',
  'Cardiology Visit','Emergency Follow-up','Specialist Consultation',
  'Telemedicine','Pediatric Visit','General Checkup','Dental Cleaning',
  'Vaccination','Physiotherapy','Routine Follow-up'
]

function Counter({ label, value, onChange }) {
  return (
    <div className="form-group">
      <label className="form-label">{label}</label>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 4 }}>
        <button 
          type="button" 
          className="btn btn-ghost btn-sm" 
          style={{ width: 32, height: 32, padding: 0, fontSize: 18 }}
          onClick={() => onChange(Math.max(0, value - 1))}
        >−</button>
        <div style={{ 
          minWidth: 40, textAlign: 'center', fontSize: 16, fontWeight: 700, 
          color: '#e2e8f0', background: 'rgba(255,255,255,0.05)', 
          padding: '4px 10px', borderRadius: 6, border: '1px solid rgba(255,255,255,0.1)' 
        }}>{value}</div>
        <button 
          type="button" 
          className="btn btn-ghost btn-sm" 
          style={{ width: 32, height: 32, padding: 0, fontSize: 18 }}
          onClick={() => onChange(value + 1)}
        >+</button>
      </div>
    </div>
  )
}

export default function ReviewQueue({ addToast }) {
  const [queue, setQueue] = useState([])
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [filter, setFilter] = useState('ALL')
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({
    patient_name: '', patient_age: '', patient_phone: '', patient_email: '',
    appointment_type: 'General Checkup', appointment_datetime: '',
    total_visits: 0, no_show_count: 0
  })

  const fetchQueue = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/queue')
      const data = await res.json()
      setQueue(data)
    } catch { addToast('Failed to load queue', 'error') }
    setLoading(false)
  }

  useEffect(() => { fetchQueue() }, [])

  const runAgent = async () => {
    setRunning(true)
    addToast('Agent is processing appointments…', 'info')
    try {
      const res = await fetch('/api/run-agent', { method: 'POST' })
      const data = await res.json()
      if (data.detail) { addToast(data.detail, 'error') }
      else { addToast(`Agent processed ${data.processed} appointment(s)`, 'success'); fetchQueue() }
    } catch { addToast('Agent failed', 'error') }
    setRunning(false)
  }

  const handleApprove = async (id) => {
    try {
      await fetch(`/api/queue/${id}/approve`, { method: 'PATCH' })
      setQueue(q => q.map(r => r.id === id ? { ...r, status: 'APPROVED' } : r))
      addToast('Reminder approved', 'success')
    } catch { addToast('Failed to approve', 'error') }
  }

  const handleEdit = async (id, editedMessage) => {
    try {
      await fetch(`/api/queue/${id}/edit`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ edited_message: editedMessage })
      })
      setQueue(q => q.map(r => r.id === id ? { ...r, edited_message: editedMessage } : r))
      addToast('Message saved', 'success')
    } catch { addToast('Failed to save edit', 'error') }
  }

  const handleDispatch = async (id) => {
    try {
      const res = await fetch(`/api/queue/${id}/dispatch`, { method: 'POST' })
      const data = await res.json()
      setQueue(q => q.map(r => r.id === id ? { ...r, status: 'DISPATCHED', dispatched_at: data.dispatched_at } : r))
      addToast('Reminder dispatched!', 'success')
    } catch { addToast('Failed to dispatch', 'error') }
  }

  const handleDelete = async (appointmentId) => {
    if (!window.confirm('Are you sure you want to delete this appointment and its reminder?')) return
    
    try {
      const res = await fetch(`/api/appointments/${appointmentId}`, { method: 'DELETE' })
      if (res.ok) {
        setQueue(q => q.filter(r => r.appointment_id !== appointmentId))
        addToast('Appointment deleted', 'success')
      } else {
        const errorData = await res.json().catch(() => ({}));
        addToast(`Failed: ${errorData.detail || res.statusText || 'Unknown error'}`, 'error')
      }
    } catch {
      addToast('Error deleting appointment', 'error')
    }
  }

  const handleCreateAppt = async (e) => {
    e.preventDefault()
    try {
      const res = await fetch('/api/appointments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...form,
          patient_age: parseInt(form.patient_age),
          appointment_datetime: new Date(form.appointment_datetime).toISOString()
        })
      })
      if (!res.ok) throw new Error()
      addToast('Appointment created!', 'success')
      setShowForm(false)
      setForm({ 
        patient_name: '', patient_age: '', patient_phone: '', patient_email: '', 
        appointment_type: 'General Checkup', appointment_datetime: '',
        total_visits: 0, no_show_count: 0
      })
    } catch { addToast('Failed to create appointment', 'error') }
  }

  const filtered = filter === 'ALL' ? queue : queue.filter(r => r.status === filter)

  const counts = {
    total: queue.length,
    pending: queue.filter(r => r.status === 'PENDING').length,
    approved: queue.filter(r => r.status === 'APPROVED').length,
    dispatched: queue.filter(r => r.status === 'DISPATCHED').length,
  }

  return (
    <div className="page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">Review Queue</h1>
          <p className="page-subtitle">AI-generated reminders awaiting staff review</p>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <button className="btn btn-ghost" id="new-appt-btn" onClick={() => setShowForm(true)}>+ New Appointment</button>
          <button
            className={`run-agent-btn ${running ? 'loading' : ''}`}
            id="run-agent-btn"
            onClick={runAgent}
            disabled={running}
          >
            <span className={running ? 'spin' : ''}>⚡</span>
            {running ? 'Running Agent…' : 'Run Agent'}
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="stats-bar">
        <div className="stat-card"><div className="stat-value stat-cyan">{counts.total}</div><div className="stat-label">Total Reminders</div></div>
        <div className="stat-card"><div className="stat-value stat-violet">{counts.pending}</div><div className="stat-label">Pending Review</div></div>
        <div className="stat-card"><div className="stat-value stat-green">{counts.approved}</div><div className="stat-label">Approved</div></div>
        <div className="stat-card"><div className="stat-value stat-amber">{counts.dispatched}</div><div className="stat-label">Dispatched</div></div>
      </div>

      {/* Filter tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
        {['ALL', 'PENDING', 'APPROVED', 'DISPATCHED'].map(f => (
          <button
            key={f}
            className={`btn btn-sm ${filter === f ? 'btn-primary' : 'btn-ghost'}`}
            id={`filter-${f.toLowerCase()}`}
            onClick={() => setFilter(f)}
          >{f}</button>
        ))}
      </div>

      {/* Cards */}
      {loading ? (
        <div className="empty-state"><div className="spin" style={{fontSize:32}}>⟳</div><div className="empty-title" style={{marginTop:16}}>Loading queue…</div></div>
      ) : filtered.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon"></div>
          <div className="empty-title">{queue.length === 0 ? 'No reminders yet' : `No ${filter} reminders`}</div>
          <div className="empty-subtitle">{queue.length === 0 ? 'Click "Run Agent" to generate AI reminders for all appointments.' : 'Try a different filter.'}</div>
        </div>
      ) : (
        filtered.map(r => (
          <ReminderCard
            key={r.id}
            reminder={r}
            onApprove={handleApprove}
            onEdit={handleEdit}
            onDispatch={handleDispatch}
            onDelete={() => handleDelete(r.appointment_id)}
          />
        ))
      )}

      {/* New Appointment Modal */}
      {showForm && (
        <div className="modal-overlay" onClick={() => setShowForm(false)}>
          <div className="modal" onClick={e => e.stopPropagation()} style={{width: 560}}>
            <div className="modal-title">+ New Appointment</div>
            <div className="modal-subtitle">Add a patient appointment to generate an AI reminder</div>
            <form onSubmit={handleCreateAppt}>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Patient Name</label>
                  <input className="form-input" required placeholder="Jane Doe" value={form.patient_name} onChange={e => setForm({...form, patient_name: e.target.value})} />
                </div>
                <div className="form-group">
                  <label className="form-label">Age</label>
                  <input className="form-input" type="number" required min="0" max="130" placeholder="45" value={form.patient_age} onChange={e => setForm({...form, patient_age: e.target.value})} />
                </div>
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label className="form-label">Phone</label>
                  <input className="form-input" placeholder="+1-555-0100" value={form.patient_phone} onChange={e => setForm({...form, patient_phone: e.target.value})} />
                </div>
                <div className="form-group">
                  <label className="form-label">Email</label>
                  <input className="form-input" type="email" placeholder="jane@email.com" value={form.patient_email} onChange={e => setForm({...form, patient_email: e.target.value})} />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Appointment Type</label>
                <select className="form-select" value={form.appointment_type} onChange={e => setForm({...form, appointment_type: e.target.value})}>
                  {APPT_TYPES.map(t => <option key={t}>{t}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Date & Time</label>
                <input className="form-input" type="datetime-local" required value={form.appointment_datetime} onChange={e => setForm({...form, appointment_datetime: e.target.value})} />
              </div>
              <div className="form-row">
                <Counter 
                  label="Past Visits" 
                  value={form.total_visits} 
                  onChange={v => setForm({...form, total_visits: v})} 
                />
                <Counter 
                  label="Past No-Shows" 
                  value={form.no_show_count} 
                  onChange={v => setForm({...form, no_show_count: v})} 
                />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-ghost" onClick={() => setShowForm(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" id="create-appt-submit">Create Appointment</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
