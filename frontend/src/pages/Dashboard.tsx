import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { TrendingUp, Users, Clock, AlertTriangle, CheckCircle, MessageSquare } from 'lucide-react'

interface Metrics {
  fcr: number
  csat: number | null
  aht_seconds: number
  churn_prob: number
  nps: number | null
  total_interactions: number
  by_channel: Record<string, number>
  sentiment_distribution: Record<string, number>
}

const COLORS = ['#534ab7', '#1d9e75', '#d85a30', '#ba7517']
const CHANNEL_COLORS: Record<string, string> = {
  web: '#534ab7', email: '#1d9e75', whatsapp: '#d85a30', voice: '#ba7517', kiosk: '#185fa5'
}

function KpiCard({ label, value, icon: Icon, color }: {
  label: string; value: string | number; icon: any; color: string
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 flex items-center gap-4">
      <div className={`p-3 rounded-lg ${color}`}>
        <Icon size={20} className="text-white" />
      </div>
      <div>
        <p className="text-sm text-gray-500">{label}</p>
        <p className="text-2xl font-semibold text-gray-900">{value}</p>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [metrics, setMetrics] = useState<Metrics | null>(null)

  useEffect(() => {
    const fetchMetrics = () =>
      fetch('/api/v1/metrics/live')
        .then(r => r.json())
        .then(setMetrics)
        .catch(() => {
          // Mock data for demo when backend is not running
          setMetrics({
            fcr: 0.84, csat: 4.3, aht_seconds: 47, churn_prob: 0.12, nps: 62,
            total_interactions: 2847,
            by_channel: { web: 1200, email: 680, whatsapp: 540, voice: 310, kiosk: 117 },
            sentiment_distribution: { positive: 1420, neutral: 980, negative: 320, frustrated: 127 },
          })
        })

    fetchMetrics()
    const id = setInterval(fetchMetrics, 5000)
    return () => clearInterval(id)
  }, [])

  if (!metrics) return (
    <div className="p-8 text-gray-400 text-sm">Loading metrics…</div>
  )

  const channelData = Object.entries(metrics.by_channel).map(([name, value]) => ({ name, value }))
  const sentimentData = Object.entries(metrics.sentiment_distribution).map(([name, value]) => ({ name, value }))

  return (
    <div className="p-8 space-y-8">
      <div>
        <h1 className="text-2xl font-semibold text-gray-900">Live KPI Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">Real-time measures of success across all channels</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-3 gap-4">
        <KpiCard label="First-Contact Resolution" value={`${(metrics.fcr * 100).toFixed(1)}%`} icon={CheckCircle} color="bg-brand-500" />
        <KpiCard label="CSAT Score"              value={metrics.csat ? `${metrics.csat}/5` : '—'}  icon={TrendingUp}   color="bg-emerald-500" />
        <KpiCard label="NPS"                     value={metrics.nps ?? '—'}                         icon={Users}        color="bg-violet-500" />
        <KpiCard label="Avg Handle Time"          value={`${metrics.aht_seconds}s`}                  icon={Clock}        color="bg-amber-500" />
        <KpiCard label="Churn Risk"              value={`${(metrics.churn_prob * 100).toFixed(1)}%`} icon={AlertTriangle} color="bg-red-500" />
        <KpiCard label="Total Interactions"       value={metrics.total_interactions.toLocaleString()} icon={MessageSquare} color="bg-sky-500" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-medium text-gray-700 mb-4">Interactions by channel</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={channelData} barSize={28}>
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {channelData.map((e, i) => (
                  <Cell key={i} fill={CHANNEL_COLORS[e.name] || '#888'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-medium text-gray-700 mb-4">Sentiment distribution</h2>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={sentimentData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false}>
                {sentimentData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
