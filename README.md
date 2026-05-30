# PriceIQ — Autonomous Pricing Intelligence Engine

An AI-powered competitor price monitoring and dynamic pricing recommendation system built for e-commerce businesses.

## What it does

PriceIQ autonomously monitors competitor websites, analyzes your historical sales data, and recommends optimal prices to maximize profit margins — all without manual intervention.

## Features

- **Autonomous Scraping** — Monitors competitor product pages on a schedule using Firecrawl
- **AI Pricing Agent** — Multi-agent LangGraph pipeline that analyzes market data and recommends optimal prices
- **Live Dashboard** — Real-time pricing charts, competitor comparisons, and one-click price approval
- **Margin Protection** — Never recommends a price below your configured minimum margin
- **Full Audit Trail** — Every recommendation, approval, and rejection is logged

## Tech Stack

**Backend**
- Python + FastAPI
- LangGraph (multi-agent orchestration)
- PostgreSQL + SQLAlchemy
- Firecrawl (web scraping)
- Groq / Llama 3.3 70B (AI reasoning)

**Frontend**
- Next.js 14 (App Router)
- Tailwind CSS + shadcn/ui
- Recharts (price history charts)

## How it works

```
Competitor URLs → Firecrawl scrapes → Groq extracts data → PostgreSQL stores
                                                                    ↓
Dashboard ← FastAPI serves ← LangGraph agent analyzes ← Sales history
```

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL

### Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m db.seed
uvicorn main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000` to access the dashboard.

## Environment Variables

Create `backend/.env`:
```
GEMINI_API_KEY=your_key
GROQ_API_KEY=your_key
FIRECRAWL_API_KEY=your_key
DATABASE_URL=postgresql://user:password@localhost:5432/pricing_db
```

Create `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## License
MIT