<p align="center">
  <img src="https://img.shields.io/badge/Theme-AI%20%7C%20Omnichannel%20CX-blueviolet?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/Stack-FastAPI%20%7C%20LangGraph%20%7C%20React-blue?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/AI-Agentic%20%7C%20RAG%20%7C%20DL-orange?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge"/>
</p>

<h1 align="center">🤖 OmniCX — Agentic AI for Seamless Omnichannel Customer Experience</h1>

<p align="center">
  <b>Reimagining connected customer journeys powered by AI with measurable outcomes that matter.</b>
</p>

---

## 🎯 Problem

Customers interact across 6+ channels — web, app, email, voice, WhatsApp, in-store — yet companies treat each touchpoint in isolation. A customer explains their issue to a chatbot, then repeats it to a call center agent, then again to a supervisor. The experience is broken, and businesses have no unified way to measure success.

## 💡 Solution

**OmniCX** is a multi-agent AI platform that:
- **Unifies** customer journeys across all channels with a shared context graph
- **Understands** customer sentiment and intent in real-time using fine-tuned DL models
- **Acts** autonomously via tool-calling agents (refund, reschedule, escalate)
- **Measures** outcomes with a live KPI dashboard (CSAT, NPS, FCR, churn risk)
- **Improves** itself through an RLHF feedback loop on low-rated interactions

---

## 🏗️ Architecture

```
Customer Channels (Web · Email · WhatsApp · Voice · Kiosk)
        │
        ▼
┌─────────────────────────────────────────┐
│        Orchestrator Agent (LangGraph)    │  ← LLM: Claude / GPT-4o
│   Intent routing · Context stitching    │
└────────────┬──────────────┬────────────┘
             │              │
    ┌─────────┴───┐    ┌────┴──────────┐
    │  Specialist Agents (async)       │
    │  Sentiment · Knowledge · Action  │
    │  Personalisation · Escalation    │
    └──────────────┬──────────────────┘
                   │
    ┌──────────────▼──────────────────┐
    │   Unified Memory & Context Store │  ← ChromaDB · Redis · Event Bus
    └──────────────┬──────────────────┘
                   │
    ┌──────────────▼──────────────────┐
    │   Real-time Analytics Engine    │  ← CSAT · NPS · Churn probability
    └──────────────┬──────────────────┘
                   │
    ┌──────────────▼──────────────────┐
    │   React Dashboard + RLHF Loop   │
    └─────────────────────────────────┘
```

---

## 🧠 Tech Stack

| Layer | Technology |
|---|---|
| **LLM / Agentic** | LangGraph, Claude 3.5 / GPT-4o, tool-calling |
| **NLP / DL** | Fine-tuned RoBERTa (sentiment), intent classifier |
| **ML** | XGBoost churn predictor, collaborative filtering |
| **RAG** | ChromaDB vector store, HuggingFace embeddings |
| **Backend** | FastAPI, WebSockets, Redis, async Python |
| **Frontend** | React 18, TypeScript, Tailwind, Zustand, Recharts |
| **Infra** | Docker Compose, GitHub Actions CI/CD |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+, Node.js 18+, Docker

### 1. Clone & configure
```bash
git clone https://github.com/your-username/omnicx.git
cd omnicx
cp .env.example .env
# Fill in your API keys in .env
```

### 2. Run everything with Docker
```bash
docker-compose up --build
```

### 3. Or run locally
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install && npm run dev
```

Open `http://localhost:5173` for the dashboard, `http://localhost:8000/docs` for the API.

---

## 📁 Project Structure

```
omnicx/
├── backend/
│   ├── agents/          # LangGraph multi-agent system
│   │   ├── orchestrator.py        # Master router agent
│   │   ├── sentiment_agent.py     # DL emotion detection
│   │   ├── knowledge_agent.py     # RAG-powered Q&A
│   │   ├── personalisation_agent.py
│   │   ├── escalation_agent.py    # Churn-risk + human handoff
│   │   └── action_agent.py        # Tool-calling (refund, book, etc.)
│   ├── core/            # Session, memory graph, event bus
│   ├── api/             # FastAPI routes + WebSocket handler
│   ├── db/              # ChromaDB + Redis clients
│   ├── services/        # RAG pipeline, metrics engine, feedback loop
│   └── ml/              # Sentiment & churn model inference
├── frontend/
│   └── src/
│       ├── components/  # Dashboard, chat, agent trace UI
│       ├── pages/       # Dashboard, CustomerView, AgentDebugger
│       ├── hooks/       # useWebSocket, useMetrics
│       └── store/       # Zustand global state
├── ml/
│   ├── sentiment/       # RoBERTa fine-tuning scripts
│   ├── churn/           # XGBoost feature engineering + training
│   ├── embeddings/      # Doc chunking & vector ingestion
│   └── notebooks/       # EDA and model evaluation
├── infra/               # Docker, Nginx configs
├── scripts/             # Seed DB, train models, ingest docs
├── tests/               # Unit + integration tests
└── docker-compose.yml
```

---

## 📊 Key Features

### ✅ Seamless Cross-Channel Context
Every interaction — regardless of channel — writes to a shared Redis session graph. Switch from web chat to a phone call: the agent already knows your history.

### ✅ Real-time Sentiment Monitoring
Fine-tuned RoBERTa scores every message for emotion intensity. Frustration above threshold → Escalation Agent activates automatically.

### ✅ RAG-Powered Knowledge Agent
Company docs, FAQs, and policies are chunked and embedded. Answers are grounded in your knowledge base, not hallucinated.

### ✅ Proactive Churn Intervention
XGBoost churn model scores every session. High-risk customers get proactive retention offers before they leave.

### ✅ Live KPI Dashboard
Real-time CSAT, NPS, First-Contact Resolution rate, average handle time, and journey completion rate — all per channel and per agent.

### ✅ RLHF Feedback Loop
Low-rated sessions are flagged and queued for fine-tuning, making the system measurably better each week.

---

## 🧪 Running Tests

```bash
cd backend
pytest tests/ -v --cov=. --cov-report=html
```

---

## 🌐 API Reference

Full OpenAPI spec at `/docs` when the backend is running. Key endpoints:

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/chat` | Send a message (any channel) |
| `WS` | `/ws/{session_id}` | Real-time chat WebSocket |
| `GET` | `/api/v1/metrics/live` | Live KPI stream |
| `GET` | `/api/v1/sessions/{id}` | Full session history |
| `POST` | `/api/v1/feedback` | Submit CSAT rating |

---

## 🏆 Hackathon Context

Built for **[Hackathon Name]** under **Theme 02: How can we use AI to deliver seamless customer experiences across channels while defining clear measures of success?**

This project directly addresses the theme by:
1. Using agentic AI to unify CX across 6 channels
2. Embedding measurable KPIs (CSAT, NPS, FCR, churn probability) as first-class citizens
3. Closing the loop with a self-improving RLHF system

---

## 👥 Team

| Name | Role |
|---|---|
| Your Name | Full-stack + AI/ML |

---

## 📄 License

MIT — see [LICENSE](LICENSE)
