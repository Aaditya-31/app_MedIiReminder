import { useState } from 'react'

const CHANNEL_ICONS = { SMS: '', EMAIL: '', PHONE_CALL: '' }
const CHANNEL_CLASS = { SMS: 'badge-sms', EMAIL: 'badge-email', PHONE_CALL: 'badge-phone' }
const CARD_CLASS = { SMS: 'card-sms', EMAIL: 'card-email', PHONE_CALL: 'card-phone' }

function formatDate(iso) {
  return new Date(iso).toLocaleString('en-US', {
    weekday: 'short', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit'
  })
}

function StatusChip({ status }) {
  const cls = { PENDING: 'chip-pending', APPROVED: 'chip-approved', DISPATCHED: 'chip-dispatched' }
  const icons = { PENDING: '', APPROVED: '', DISPATCHED: '' }
  return (
    <span className={`status-chip ${cls[status] || 'chip-pending'}`}>
      {status}
    </span>
  )
}

export default function ReminderCard({ reminder, onApprove, onEdit, onDispatch, onDelete }) {
  const [editing, setEditing] = useState(false)
  const [editText, setEditText] = useState('')
  const [showDispatch, setShowDispatch] = useState(false)

  const isDispatched = reminder.status === 'DISPATCHED'
  const isApproved = reminder.status === 'APPROVED'
  const displayMessage = reminder.edited_message || reminder.message
  const channelClass = CARD_CLASS[reminder.channel] || 'card-sms'

  const handleEditSave = async () => {
    await onEdit(reminder.id, editText)
    setEditing(false)
  }

  const handleEditStart = () => {
    setEditText(displayMessage)
    setEditing(true)
  }

  return (
    <>
      <div className={`reminder-card ${channelClass} ${isDispatched ? 'dispatched' : ''}`}>
        {/* Header */}
        <div className="card-header">
          <div className="card-patient">
            <div className="patient-name">{reminder.patient?.name}</div>
            <div className="patient-meta">
              <span className="meta-item">Age {reminder.patient?.age}</span>
              <span className="meta-item">{reminder.patient?.phone}</span>
              <span className="meta-item">{reminder.patient?.email}</span>
            </div>
          </div>
          <div className="card-badges">
            <span className={`channel-badge ${CHANNEL_CLASS[reminder.channel]}`}>
              {reminder.channel?.replace('_', ' ')}
            </span>
            <StatusChip status={reminder.status} />
            {!isDispatched && (
              <button 
                className="btn btn-ghost btn-sm" 
                onClick={(e) => { e.stopPropagation(); onDelete() }}
                style={{ color: '#ef4444', marginLeft: 8, padding: '4px' }}
                title="Delete Appointment"
              >
                Delete
              </button>
            )}
          </div>
        </div>

        {/* Appointment Info */}
        <div className="appt-info">
          <div className="appt-info-item">
            <span className="appt-label">Type</span>
            <span className="appt-value">{reminder.appointment?.appointment_type}</span>
          </div>
          <div className="appt-info-item">
            <span className="appt-label">Scheduled</span>
            <span className="appt-value">{formatDate(reminder.appointment?.appointment_datetime)}</span>
          </div>
          <div className="appt-info-item">
            <span className="appt-label">Total Visits</span>
            <span className="appt-value">{reminder.history?.total_visits ?? '—'}</span>
          </div>
          <div className="appt-info-item">
            <span className="appt-label">No-Shows</span>
            <span className="appt-value">{reminder.history?.no_show_count ?? '—'}</span>
          </div>
        </div>

        {/* AI Reasoning */}
        <div className="reasoning-section">
          <div className="reasoning-title">
            AI REASONING
          </div>
          <div className="reasoning-list">
            {(reminder.reasoning || [])
              .filter(r => !r.includes('[Note: LLM') && !r.includes('RateLimitError'))
              .map((r, i) => (
                <div key={i} className="reasoning-item">
                  <div className="reason-dot" />
                  <span>{r}</span>
                </div>
              ))}
          </div>
        </div>

        {/* Message */}
        <div className="message-section">
          <div className="message-label">
            {reminder.edited_message ? 'EDITED MESSAGE' : 'AI DRAFTED MESSAGE'}
          </div>
          {editing ? (
            <textarea
              className="message-textarea"
              value={editText}
              onChange={e => setEditText(e.target.value)}
              id={`edit-msg-${reminder.id}`}
            />
          ) : (
            <div className="message-text">{displayMessage}</div>
          )}
        </div>

        {/* Actions */}
        {!isDispatched && (
          <div className="card-actions">
            {editing ? (
              <>
                <button className="btn btn-primary btn-sm" onClick={handleEditSave}>Save</button>
                <button className="btn btn-ghost btn-sm" onClick={() => setEditing(false)}>Cancel</button>
              </>
            ) : (
              <>
                <button
                  className="btn btn-ghost btn-sm"
                  id={`edit-btn-${reminder.id}`}
                  onClick={handleEditStart}
                >Edit</button>
                {!isApproved && (
                  <button
                    className="btn btn-success btn-sm"
                    id={`approve-btn-${reminder.id}`}
                    onClick={() => onApprove(reminder.id)}
                  >Approve</button>
                )}
                <button
                  className="btn btn-primary btn-sm"
                  id={`dispatch-btn-${reminder.id}`}
                  onClick={() => setShowDispatch(true)}
                >Dispatch</button>
              </>
            )}
          </div>
        )}

        {isDispatched && reminder.dispatched_at && (
          <div className="meta-item" style={{ marginTop: 8 }}>
            Dispatched at {formatDate(reminder.dispatched_at)}
          </div>
        )}
      </div>

      {/* Dispatch Confirm Modal */}
      {showDispatch && (
        <div className="modal-overlay" onClick={() => setShowDispatch(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-title">Confirm Dispatch</div>
            <div className="modal-subtitle">
              You are about to mark this reminder as <strong>DISPATCHED</strong>.<br/>
              Nothing will actually be sent — this only updates the database record.
            </div>
            <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 8, padding: '12px 16px', marginBottom: 8 }}>
              <div style={{ fontSize: 13, color: '#94a3b8', marginBottom: 6 }}>Patient: <strong style={{color:'#e2e8f0'}}>{reminder.patient?.name}</strong></div>
              <div style={{ fontSize: 13, color: '#94a3b8', marginBottom: 6 }}>Channel: <strong style={{color:'#e2e8f0'}}>{reminder.channel?.replace('_',' ')}</strong></div>
              <div style={{ fontSize: 13, color: '#94a3b8' }}>Appointment: <strong style={{color:'#e2e8f0'}}>{reminder.appointment?.appointment_type}</strong></div>
            </div>
            <div className="modal-actions">
              <button className="btn btn-ghost" onClick={() => setShowDispatch(false)}>Cancel</button>
              <button
                className="btn btn-primary"
                id={`confirm-dispatch-${reminder.id}`}
                onClick={() => { onDispatch(reminder.id); setShowDispatch(false) }}
              >Confirm Dispatch</button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
