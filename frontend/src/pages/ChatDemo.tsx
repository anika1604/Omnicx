import { useState, useRef, useEffect } from 'react'
import { Send, Wifi, WifiOff } from 'lucide-react'

type Channel = 'web' | 'email' | 'whatsapp' | 'voice' | 'kiosk'

interface Message {
  id:       string
  role:     'user' | 'assistant'
  content:  string
  intent?:  string
  sentiment?: string
  escalate?: boolean
}

const CHANNEL_LABELS: Record<Channel, string> = {
  web: '🌐 Web', email: '📧 Email', whatsapp: '💬 WhatsApp', voice: '📞 Voice', kiosk: '🖥️ Kiosk'
}

const SENTIMENT_COLORS: Record<string, string> = {
  positive:   'bg-emerald-100 text-emerald-700',
  neutral:    'bg-gray-100 text-gray-600',
  negative:   'bg-orange-100 text-orange-700',
  frustrated: 'bg-red-100 text-red-700',
}

export default function ChatDemo() {
  const [messages,   setMessages]   = useState<Message[]>([])
  const [input,      setInput]      = useState('')
  const [channel,    setChannel]    = useState<Channel>('web')
  const [customerId, setCustomerId] = useState('demo-customer-001')
  const [sessionId,  setSessionId]  = useState<string | null>(null)
  const [loading,    setLoading]    = useState(false)
  const [wsStatus,   setWsStatus]   = useState<'connected' | 'disconnected'>('disconnected')
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const sendMessage = async () => {
    if (!input.trim() || loading) return
    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: input }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch('/api/v1/chat/', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message:     input,
          session_id:  sessionId,
          customer_id: customerId,
          channel,
        }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error('API error')
      setSessionId(data.session_id)
      setMessages(prev => [...prev, {
        id:        Date.now().toString() + 'a',
        role:      'assistant',
        content:   data.response,
        intent:    data.intent,
        sentiment: data.sentiment,
        escalate:  data.should_escalate,
      }])
    } catch {
      // Mock response when backend offline
      setMessages(prev => [...prev, {
        id:      Date.now().toString() + 'a',
        role:    'assistant',
        content: `[Demo mode] I received your message: "${input}". Backend is not running — this is a mock response showing how OmniCX would reply across the ${channel} channel.`,
        intent:  'query',
        sentiment: 'neutral',
        escalate: false,
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">Omnichannel Chat Demo</h1>
          <p className="text-xs text-gray-500">Switch channels mid-conversation — context persists</p>
        </div>
        <div className="flex items-center gap-4">
          <input
            className="text-xs border border-gray-300 rounded-lg px-3 py-1.5 w-44"
            value={customerId}
            onChange={e => setCustomerId(e.target.value)}
            placeholder="Customer ID"
          />
          <div className="flex gap-1">
            {(Object.keys(CHANNEL_LABELS) as Channel[]).map(ch => (
              <button
                key={ch}
                onClick={() => setChannel(ch)}
                className={`text-xs px-3 py-1.5 rounded-full transition-colors ${
                  channel === ch ? 'bg-brand-500 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {CHANNEL_LABELS[ch]}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 text-sm mt-20">
            <p className="text-4xl mb-3">💬</p>
            <p>Start a conversation. Switch channels mid-way to see context persistence in action.</p>
          </div>
        )}
        {messages.map(msg => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-lg ${msg.role === 'user' ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
              <div className={`rounded-2xl px-4 py-3 text-sm ${
                msg.role === 'user'
                  ? 'bg-brand-500 text-white rounded-br-sm'
                  : 'bg-white border border-gray-200 text-gray-800 rounded-bl-sm'
              }`}>
                {msg.content}
              </div>
              {msg.role === 'assistant' && (
                <div className="flex gap-1.5 flex-wrap">
                  {msg.intent && (
                    <span className="text-xs bg-violet-50 text-violet-600 px-2 py-0.5 rounded-full">
                      {msg.intent}
                    </span>
                  )}
                  {msg.sentiment && (
                    <span className={`text-xs px-2 py-0.5 rounded-full ${SENTIMENT_COLORS[msg.sentiment] || 'bg-gray-100'}`}>
                      {msg.sentiment}
                    </span>
                  )}
                  {msg.escalate && (
                    <span className="text-xs bg-red-100 text-red-600 px-2 py-0.5 rounded-full">
                      🚨 escalated
                    </span>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-sm px-4 py-3">
              <div className="flex gap-1">
                {[0, 1, 2].map(i => (
                  <div key={i} className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: `${i * 0.15}s` }} />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Input */}
      <div className="bg-white border-t border-gray-200 px-6 py-4">
        <div className="flex gap-3">
          <input
            className="flex-1 border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
            placeholder={`Message via ${CHANNEL_LABELS[channel]}…`}
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            className="bg-brand-500 hover:bg-brand-600 disabled:opacity-40 text-white rounded-xl px-4 py-2.5 transition-colors"
          >
            <Send size={16} />
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-2">
          Session: {sessionId ?? 'not started'} · Channel: {channel}
        </p>
      </div>
    </div>
  )
}
