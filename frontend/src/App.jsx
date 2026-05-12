import { useState } from 'react'
import Sidebar from './components/Sidebar'
import ReviewQueue from './pages/ReviewQueue'
import Appointments from './pages/Appointments'
import ToastContainer from './components/ToastContainer'
import ChatBot from './components/ChatBot'
import CursorGlow from './components/CursorGlow'

export default function App() {
  const [page, setPage] = useState('queue')
  const [toasts, setToasts] = useState([])

  const addToast = (message, type = 'info') => {
    const id = Date.now()
    setToasts(t => [...t, { id, message, type }])
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 3500)
  }

  return (
    <div className="app-shell">
      <Sidebar page={page} setPage={setPage} />
      <div className="main-content">
        {page === 'queue'
          ? <ReviewQueue addToast={addToast} />
          : <Appointments addToast={addToast} />
        }
      </div>
      <ToastContainer toasts={toasts} />
      <ChatBot />
      <CursorGlow />
    </div>
  )
}
