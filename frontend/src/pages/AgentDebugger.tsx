import { useState } from 'react'
import { Brain, Zap, BookOpen, AlertTriangle, Wrench } from 'lucide-react'

const AGENTS = [
  { name: 'Orchestrator',     icon: Brain,         color: 'text-violet-600',  bg: 'bg-violet-50',  desc: 'LangGraph router — routes intent and merges results' },
  { name: 'Sentiment Agent',  icon: Zap,           color: 'text-amber-600',   bg: 'bg-amber-50',   desc: 'Fine-tuned RoBERTa — scores emotion intensity' },
  { name: 'Knowledge Agent',  icon: BookOpen,      color: 'text-sky-600',     bg: 'bg-sky-50',     desc: 'RAG pipeline — ChromaDB + LLM grounded answers' },
  { name: 'Escalation Agent', icon: AlertTriangle, color: 'text-red-600',     bg: 'bg-red-50',     desc: 'Churn risk + human handoff decision logic' },
  { name: 'Action Agent',     icon: Wrench,        color: 'text-emerald-600', bg: 'bg-emerald-50', desc: 'Tool-calling — refund, rebook, cancel, track' },
]

export default function AgentDebugger() {
  const [trace, setTrace] = useState<any>(null)
  const [testMsg, setTestMsg] = useState("I'm really frustrated, I need a refund immediately!")
  const [loading, setLoading] = useState(false)

  const runTest = async () => {
    setLoading(true)
    try {
      const res = await fetch('/api/v1/chat/', {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: testMsg, customer_id: 'debugger-test', channel: 'web' }),
      })
      const data = await res.json()
      setTrace(data)
    } catch {
      setTrace({
        intent: 'complaint', sentiment: 'frustrated', should_escalate: true,
        response: "I completely understand your frustration and I sincerely apologize. I've initiated your refund and flagged your case as high priority.",
        agent_trace: {
          sentiment:  { label: 'frustrated', score: 0.91, trigger_escalation: true },
          knowledge:  { answer: 'Refund policy: full refund within 30 days.', sources_used: 2 },
          escalation: { should_escalate: true, reasons: ['frustrated_sentiment'], priority: 'HIGH' },
          action:     { action: 'refund', message: "Refund initiated. You'll see it in 3–5 business days.", stub: true },
        },
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Agent Debugger</h1>
        <p className="text-sm text-gray-500 mt-1">Inspect each agent's reasoning in real-time</p>
      </div>

      {/* Agent cards */}
      <div className="grid grid-cols-5 gap-3">
        {AGENTS.map(a => (
          <div key={a.name} className={`${a.bg} rounded-xl p-4 border border-gray-100`}>
            <a.icon className={`${a.color} mb-2`} size={20} />
            <p className="text-sm font-medium text-gray-800">{a.name}</p>
            <p className="text-xs text-gray-500 mt-1">{a.desc}</p>
          </div>
        ))}
      </div>

      {/* Test runner */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h2 className="text-sm font-medium mb-3">Test a message</h2>
        <div className="flex gap-3">
          <input
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            value={testMsg}
            onChange={e => setTestMsg(e.target.value)}
          />
          <button
            onClick={runTest}
            disabled={loading}
            className="bg-brand-500 hover:bg-brand-600 disabled:opacity-40 text-white text-sm rounded-lg px-4 py-2 transition-colors"
          >
            {loading ? 'Running…' : 'Run agents ↗'}
          </button>
        </div>
      </div>

      {/* Trace output */}
      {trace && (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: 'Intent',    value: trace.intent },
              { label: 'Sentiment', value: trace.sentiment },
              { label: 'Escalate', value: trace.should_escalate ? '🚨 Yes' : '✅ No' },
            ].map(({ label, value }) => (
              <div key={label} className="bg-white rounded-xl border border-gray-200 p-4">
                <p className="text-xs text-gray-500">{label}</p>
                <p className="text-sm font-semibold mt-1">{value}</p>
              </div>
            ))}
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <p className="text-xs text-gray-500 mb-2">Final response</p>
            <p className="text-sm text-gray-800">{trace.response}</p>
          </div>

          <div className="bg-gray-900 rounded-xl p-5">
            <p className="text-xs text-gray-400 mb-3">Agent trace (JSON)</p>
            <pre className="text-xs text-green-400 overflow-auto max-h-72">
              {JSON.stringify(trace.agent_trace, null, 2)}
            </pre>
          </div>
        </div>
      )}
    </div>
  )
}
