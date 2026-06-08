import { create } from 'zustand'

interface Message {
  id:        string
  role:      'user' | 'assistant'
  content:   string
  channel:   string
  intent?:   string
  sentiment?: string
  escalate?: boolean
}

interface SessionState {
  sessionId:   string | null
  customerId:  string
  channel:     string
  messages:    Message[]
  setSession:  (id: string) => void
  setChannel:  (ch: string) => void
  addMessage:  (msg: Message) => void
  reset:       () => void
}

export const useSessionStore = create<SessionState>(set => ({
  sessionId:  null,
  customerId: 'demo-customer-001',
  channel:    'web',
  messages:   [],
  setSession: id  => set({ sessionId: id }),
  setChannel: ch  => set({ channel: ch }),
  addMessage: msg => set(s => ({ messages: [...s.messages, msg] })),
  reset:      ()  => set({ sessionId: null, messages: [] }),
}))
