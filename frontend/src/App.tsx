import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import ChatDemo from './pages/ChatDemo'
import AgentDebugger from './pages/AgentDebugger'
import { LayoutDashboard, MessageSquare, Bot } from 'lucide-react'

const NAV = [
  { to: '/',         label: 'Dashboard',      icon: LayoutDashboard },
  { to: '/chat',     label: 'Chat Demo',      icon: MessageSquare },
  { to: '/debugger', label: 'Agent Debugger', icon: Bot },
]

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-gray-50 text-gray-900">
        <aside className="w-56 bg-brand-900 text-white flex flex-col" style={{backgroundColor: '#26215c'}}>
          <div className="px-6 py-5" style={{borderBottom: '1px solid #3c3489'}}>
            <span className="text-lg font-semibold tracking-tight">OmniCX</span>
            <p className="text-xs mt-0.5" style={{color: '#cecbf6'}}>Agentic AI Platform</p>
          </div>
          <nav className="flex-1 py-4 space-y-1 px-3">
            {NAV.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                    isActive ? 'text-white' : 'text-purple-200 hover:text-white'
                  }`
                }
                style={({ isActive }) => isActive ? { backgroundColor: '#534ab7' } : {}}
              >
                <Icon size={16} />
                {label}
              </NavLink>
            ))}
          </nav>
          <div className="px-6 py-4 text-xs" style={{color: '#cecbf6', borderTop: '1px solid #3c3489'}}>
            Theme 02 · Hackathon Build
          </div>
        </aside>
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/"         element={<Dashboard />} />
            <Route path="/chat"     element={<ChatDemo />} />
            <Route path="/debugger" element={<AgentDebugger />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}