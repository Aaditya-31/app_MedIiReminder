export default function Sidebar({ page, setPage }) {
  const nav = [
    { id: 'queue', icon: '', label: 'Review Queue' },
    { id: 'appointments', icon: '', label: 'Appointments' },
  ]

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h1>MediReminder</h1>
        <p>AI REMINDER PLATFORM</p>
      </div>

      <nav>
        {nav.map(item => (
          <div
            key={item.id}
            id={`nav-${item.id}`}
            className={`nav-item ${page === item.id ? 'active' : ''}`}
            onClick={() => setPage(item.id)}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </div>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="status-dot">
          <div className="dot" />
          Agent Online
        </div>
      </div>
    </aside>
  )
}
