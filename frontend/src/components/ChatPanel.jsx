import { useState, useRef, useEffect } from 'react'
import { Send, MessageCircle, Trash2 } from 'lucide-react'
import { api } from '../api/client'
import './ChatPanel.css'

export default function ChatPanel({ onQueryResult }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hi! I can help you analyze the Order to Cash process. Try asking:\n\n• "Find order 740506"\n• "Show me customer 310000108"\n• "Trace the flow of order 740506"\n• "Find the journal entry for billing document 91150187"'
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage = input.trim()
    setInput('')
    
    // Add user message
    setMessages(prev => [...prev, { role: 'user', content: userMessage }])
    setLoading(true)

    try {
      const response = await api.chat(userMessage)
      
      // Extract SQL if present in the content
      const sqlRegex = /```sql\n([\s\S]*?)```/
      const match = response.response.match(sqlRegex)
      const cleanContent = response.response.replace(sqlRegex, '').trim()
      const sql = match ? match[1] : null

      // Add assistant response
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: cleanContent,
        sql: sql
      }])

      // Pass query result to parent
      if (response.query_result) {
        onQueryResult(response.query_result)
      }
    } catch (error) {
      console.error('Chat error:', error)
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I encountered an error. Please try again.' 
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleClearChat = async () => {
    try {
      await api.clearChat()
      setMessages([
        {
          role: 'assistant',
          content: 'Chat history cleared. How can I help you?'
        }
      ])
    } catch (error) {
      console.error('Error clearing chat:', error)
    }
  }

  const quickQueries = [
    'Find order 740506',
    'Show customer analytics',
    'Trace delivery flow',
  ]

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <div className="chat-title-group">
          <span className="chat-subtitle">CHAT WITH Graph AI</span>
          <h2 className="chat-main-title">Order to Cash</h2>
        </div>
        <button className="clear-btn" onClick={handleClearChat} title="Clear chat">
          <Trash2 size={16} />
        </button>
      </div>

      <div className="messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message-wrapper ${msg.role}`}>
            <div className="message-avatar">
              {msg.role === 'assistant' ? 'D' : '👤'}
            </div>
            <div className="message-bubble">
              <div className="message-sender">
                {msg.role === 'assistant' ? 'Graph Agent' : 'You'}
              </div>
              <div className="message-text">
                {msg.content.split('\n').map((line, i) => (
                  <p key={i}>{line}</p>
                ))}
                {msg.sql && (
                  <div className="sql-container">
                    <details>
                      <summary>^ View SQL</summary>
                      <pre className="sql-code"><code>{msg.sql}</code></pre>
                    </details>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        
        {loading && (
          <div className="message-wrapper assistant">
            <div className="message-avatar">D</div>
            <div className="message-bubble">
              <div className="message-sender">Graph Agent</div>
              <div className="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-container" onSubmit={handleSubmit}>
        <div className="input-wrapper">
          <input
            type="text"
            className="chat-input"
            placeholder="Analyze anything..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
          />
          <button 
            type="submit" 
            className="send-button"
            disabled={!input.trim() || loading}
          >
            <Send size={18} />
          </button>
        </div>
      </form>
    </div>
  )
}
