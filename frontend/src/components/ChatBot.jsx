import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'

export default function ChatBot() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hi! I\'m your MediReminder AI Assistant. Ask me about appointments, patients, or reminder queue status.' }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async () => {
    const text = input.trim()
    if (!text || loading) return

    const userMsg = { role: 'user', content: text }
    const newMsgs = [...messages, userMsg]
    setMessages(newMsgs)
    setInput('')
    setLoading(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: newMsgs.filter(m => m.role !== 'system') })
      })
      const data = await res.json()
      setMessages(m => [...m, { role: 'assistant', content: data.reply || data.detail || 'No response' }])
    } catch {
      setMessages(m => [...m, { role: 'assistant', content: '⚠️ Could not reach the server.' }])
    }
    setLoading(false)
  }

  const onKey = e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send() }
  }

  return (
    <>
      <button className="chat-fab" id="chat-fab-btn" onClick={() => setOpen(o => !o)} title="AI Assistant">
        {open ? '✕' : '🤖'}
      </button>

      {open && (
        <div className="chat-panel" id="chat-panel">
          <div className="chat-header">
            <div className="chat-title">🤖 MediReminder AI Assistant</div>
            <button className="chat-close" onClick={() => setOpen(false)}>✕</button>
          </div>

          <div className="chat-messages" id="chat-messages">
            {messages.map((m, i) => (
              <div key={i} className={`chat-bubble ${m.role === 'user' ? 'bubble-user' : 'bubble-assistant'}`}>
                <ReactMarkdown>{m.content}</ReactMarkdown>
              </div>
            ))}
            {loading && (
              <div className="chat-bubble bubble-assistant bubble-typing">typing...</div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="chat-input-row">
            <textarea
              id="chat-input"
              className="chat-input"
              rows={1}
              placeholder="Ask about appointments..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={onKey}
            />
            <button className="chat-send" id="chat-send-btn" onClick={send} disabled={loading || !input.trim()}>
              ➤
            </button>
          </div>
        </div>
      )}
    </>
  )
}
