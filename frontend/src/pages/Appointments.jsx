import { useState, useEffect } from 'react'

function formatDate(iso) {
  return new Date(iso).toLocaleString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })
}

function getStatusColor(status) {
  if (status === 'SCHEDULED') return '#00d4ff'
  if (status === 'COMPLETED') return '#10b981'
  if (status === 'NO_SHOW') return '#ef4444'
  return '#64748b'
}

function getStatusBg(status) {
  if (status === 'SCHEDULED') return 'rgba(0,212,255,0.1)'
  if (status === 'COMPLETED') return 'rgba(16,185,129,0.1)'
  if (status === 'NO_SHOW') return 'rgba(239,68,68,0.1)'
  return 'rgba(255,255,255,0.06)'
}

export default function Appointments({ addToast }) {
  const [appointments, setAppointments] = useState([])
  const [loading, setLoading] = useState(true)

  const fetchAppointments = () => {
    setLoading(true)
    fetch('/api/appointments')
      .then(r => r.json())
      .then(data => { setAppointments(data); setLoading(false) })
      .catch(() => { addToast('Failed to load appointments', 'error'); setLoading(false) })
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this appointment?')) return
    
    try {
      const res = await fetch(`/api/appointments/${id}`, { method: 'DELETE' })
      if (res.ok) {
        setAppointments(prev => prev.filter(a => a.id !== id))
        addToast('Appointment deleted', 'success')
      } else {
        const errorData = await res.json().catch(() => ({}));
        addToast(`Failed: ${errorData.detail || res.statusText || 'Unknown error'}`, 'error')
      }
    } catch {
      addToast('Error deleting appointment', 'error')
    }
  }

  useEffect(() => {
    fetchAppointments()
  }, [])


  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Appointments</h1>
          <p className="page-subtitle">All scheduled patient appointments and risk profiles</p>
        </div>
      </div>

      {loading ? (
        <div className="empty-state"><div className="spin" style={{fontSize:32}}>⟳</div></div>
      ) : (
        <div className="glass-card" style={{overflow:'hidden'}}>
          <table className="data-table">
            <thead>
              <tr>
                <th>Patient</th>
                <th>Age</th>
                <th>Type</th>
                <th>Scheduled</th>
                <th>Visits / No-Shows</th>
                <th>Status</th>
                <th style={{textAlign:'right'}}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {appointments.map(appt => (
                <tr key={appt.id}>
                  <td>
                    <div style={{fontWeight:600, color:'#e2e8f0'}}>{appt.patient?.name}</div>
                    <div style={{fontSize:11, color:'#64748b'}}>{appt.patient?.email}</div>
                  </td>
                  <td style={{color:'#94a3b8'}}>{appt.patient?.age}</td>
                  <td>
                    <span style={{
                      fontSize:12, fontWeight:600, padding:'3px 10px',
                      borderRadius:20, background:'rgba(255,255,255,0.06)',
                      border:'1px solid rgba(255,255,255,0.1)', color:'#e2e8f0'
                    }}>{appt.appointment_type}</span>
                  </td>
                  <td style={{color:'#94a3b8', fontSize:12}}>{formatDate(appt.appointment_datetime)}</td>
                  <td style={{color:'#94a3b8'}}>
                    {appt.history?.total_visits ?? '—'} visits / {appt.history?.no_show_count ?? '—'} no-shows
                  </td>
                  <td>
                    <span style={{
                      fontSize:11, fontWeight:700, padding:'3px 10px',
                      borderRadius:20, letterSpacing:'0.5px',
                      background: getStatusBg(appt.status),
                      color: getStatusColor(appt.status),
                      border: `1px solid ${getStatusColor(appt.status)}55`
                    }}>{appt.status}</span>
                  </td>
                  <td style={{textAlign:'right'}}>
                    <button 
                      className="btn btn-ghost btn-sm" 
                      onClick={() => handleDelete(appt.id)}
                      style={{ color: '#ef4444', padding: '4px 8px' }}
                      title="Delete Appointment"
                    >
                      Delete
                    </button>
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
