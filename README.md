# 🚀 ET Markets Intelligence Layer

**AI Signal Detection for Retail Investors — Hackathon Prototype**

An AI-powered financial intelligence system that collects data, runs NLP + anomaly detection, generates market signals with AI explanations, and displays everything on a real-time dashboard.

![Architecture](https://img.shields.io/badge/Architecture-Modular-blue) ![Python](https://img.shields.io/badge/Python-3.11+-yellow) ![React](https://img.shields.io/badge/React-18-cyan) ![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)

---

## 📋 System Architecture

```
Data Sources (Yahoo Finance, NewsAPI, Reddit/Twitter)
        ↓
Data Ingestion Layer (data_ingestion.py)
        ↓
AI Signal Detection Engine
  ├── NLP Detector (FinBERT / VADER)
  ├── Anomaly Detector (Z-score, Bollinger, VWAP)
  ├── Pattern Detector (Candlestick patterns)
  ├── Options Analyzer (PCR, Max Pain, IV Skew)
  └── Social Sentiment (Reddit, Twitter/X)
        ↓
Signal Scoring Engine (Weighted multi-source fusion)
        ↓
AI Explanation Generator (OpenRouter LLM / Rule-based fallback)
        ↓
API Layer (FastAPI + WebSocket)
        ↓
Frontend Dashboard (React + Recharts + Framer Motion)
```

---

## ⚡ Quick Start (5 minutes)

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
# source venv/bin/activate

# Install lightweight dependencies (no ML models)
pip install -r requirements-lite.txt

# Start the API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The backend starts with **mock data** by default — no API keys needed.

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

### 3. Open Dashboard

Visit **http://localhost:5173** in your browser.

---

## 🔧 Configuration

All configuration lives in `backend/.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `MOCK_DATA` | `true` | Use mock data (no API keys needed) |
| `USE_FINBERT` | `false` | Enable FinBERT NLP (downloads ~500MB model) |
| `OPENROUTER_API_KEY` | set | LLM for AI explanations (falls back to templates) |
| `NEWSAPI_KEY` | `demo` | NewsAPI.org key for live news |
| `ALPHA_VANTAGE_KEY` | `demo` | Alpha Vantage for live stock data |

**To enable live data:** Set `MOCK_DATA=false` and add real API keys.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check + status |
| `GET` | `/signals` | List all AI signals (filterable by risk, sector) |
| `GET` | `/signals/top` | Top N signals by confidence |
| `GET` | `/signals/{stock}` | Signals for a specific stock |
| `POST` | `/signals/analyze` | Trigger fresh signal detection |
| `GET` | `/news` | Processed news articles |
| `GET` | `/heatmap` | Sector heatmap data |
| `GET` | `/portfolio` | Portfolio with P&L |
| `GET` | `/options/{stock}` | Options chain + analysis |
| `GET` | `/backtest/all` | All backtest results |
| `POST` | `/chat` | AI chatbot (SSE streaming) |
| `GET` | `/alerts` | Alert history |
| `WS` | `/ws/signals` | Live signal WebSocket stream |

**Interactive docs:** http://localhost:8000/docs

---

## 🧠 AI Modules

### 1. NLP Signal Detector (`signal_detector.py`)
- FinBERT sentiment analysis (or VADER fallback)
- Named Entity Recognition via spaCy
- Signal classification: EarningsRisk, InsiderActivity, SentimentShift, etc.

### 2. Anomaly Detector (`anomaly_detector.py`)
- Z-score on volume and price returns
- Bollinger Band breach detection
- Rolling volatility regime changes
- VWAP deviation alerts

### 3. Pattern Detector (`pattern_detector.py`)
- Candlestick pattern recognition (Hammer, Engulfing, Doji, etc.)
- Volume confirmation logic
- Trend context analysis

### 4. Signal Scoring Engine (`signal_scoring.py`)
- Multi-source weighted fusion (NLP 30%, Candlestick 20%, Anomaly 20%, Options 15%, Social 15%)
- Corroboration bonus for multi-detector agreement
- Risk classification: High (≥80%), Medium (60-79%), Low (<60%)

### 5. AI Explanation Agent (`explanation_agent.py`)
- OpenRouter LLM (gpt-oss-20b) for natural language explanations
- SEBI-analyst tone: never says "buy/sell"
- Rule-based template fallback when LLM unavailable

---

## 🎨 Frontend Dashboard

| Tab | Feature |
|-----|---------|
| **Signal Radar** | Filterable signal cards with confidence rings |
| **Sector Heatmap** | NSE sector performance with signal overlays |
| **Charts** | Interactive candlestick charts (TradingView-style) |
| **Options Chain** | PCR, Max Pain, IV analysis |
| **Portfolio** | Holdings with live P&L tracking |
| **Backtest** | Historical signal performance |
| **Alerts** | Configurable alert management |
| **AI Chat** | Conversational market assistant |

---

## 📁 Project Structure

```
et/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI entry point + WebSocket
│   │   ├── database.py                # SQLAlchemy async setup
│   │   ├── models.py                  # ORM models
│   │   ├── schemas.py                 # Pydantic schemas
│   │   ├── state.py                   # In-memory app state
│   │   ├── api/
│   │   │   ├── routes_signals.py      # Signal CRUD + analysis trigger
│   │   │   ├── routes_portfolio.py    # Portfolio management
│   │   │   ├── routes_heatmap.py      # Heatmap + news + patterns
│   │   │   ├── routes_chat.py         # SSE chatbot streaming
│   │   │   ├── routes_alerts.py       # Alert config + dispatch
│   │   │   ├── routes_backtest.py     # Backtesting engine
│   │   │   └── routes_options.py      # Options chain analysis
│   │   ├── ingestion/
│   │   │   ├── data_ingestion.py      # OHLCV + news fetching
│   │   │   ├── options_ingestion.py   # NSE options chain
│   │   │   └── social_ingestion.py    # Reddit/Twitter sentiment
│   │   ├── signals/
│   │   │   ├── signal_detector.py     # FinBERT NLP pipeline
│   │   │   ├── anomaly_detector.py    # Statistical anomaly detection
│   │   │   ├── pattern_detector.py    # Candlestick patterns
│   │   │   ├── options_analyzer.py    # Options flow analysis
│   │   │   └── social_sentiment.py    # Social media scoring
│   │   ├── scoring/
│   │   │   ├── signal_scoring.py      # Multi-source fusion
│   │   │   └── backtest_engine.py     # Historical backtesting
│   │   ├── intelligence/
│   │   │   ├── explanation_agent.py   # LLM explanation generator
│   │   │   └── chatbot_agent.py       # Conversational AI agent
│   │   ├── alerts/
│   │   │   ├── alert_engine.py        # Alert dispatch logic
│   │   │   ├── email_sender.py        # SendGrid integration
│   │   │   └── whatsapp_sender.py     # Twilio WhatsApp
│   │   └── portfolio/
│   │       └── portfolio_tracker.py   # P&L calculation
│   ├── mock_data/                     # Example datasets
│   ├── .env                           # Configuration
│   ├── requirements.txt               # Full dependencies
│   └── requirements-lite.txt          # Quick-start (no ML)
│
└── frontend/
    ├── src/
    │   ├── App.jsx                    # Main app + sidebar + routing
    │   ├── index.css                  # Premium design system
    │   ├── components/
    │   │   ├── SignalCard.jsx          # Signal card with modal
    │   │   ├── SignalRadar.jsx         # Signal grid + filters
    │   │   ├── SectorHeatmap.jsx       # Sector performance grid
    │   │   ├── CandlestickChart.jsx    # TradingView-style chart
    │   │   ├── OptionsChain.jsx        # Options analysis view
    │   │   ├── PortfolioView.jsx       # Holdings + P&L
    │   │   ├── BacktestView.jsx        # Backtest results
    │   │   ├── AlertManager.jsx        # Alert configuration
    │   │   ├── ChatbotPanel.jsx        # AI chat slide-out
    │   │   └── LiveAlertBanner.jsx     # Real-time alert strip
    │   ├── store/
    │   │   └── useStore.js             # Zustand global state
    │   └── hooks/
    │       ├── useWebSocket.js         # WebSocket auto-reconnect
    │       └── usePortfolio.js         # Portfolio data fetcher
    ├── package.json
    └── vite.config.js                  # Dev proxy → FastAPI
```

---

## 🔄 Live Demo Flow

```
1. News article arrives (mock or NewsAPI)
2. NLP detector classifies sentiment + signal type
3. Anomaly detector checks price/volume stats
4. Signal scoring engine fuses all detector outputs
5. AI explanation agent generates investor-friendly summary
6. Signal stored + broadcast via WebSocket
7. Dashboard displays real-time alert banner
8. User clicks signal card → sees full AI explanation
9. User asks AI chatbot for further analysis
```

---

## 🏗️ Full Dependencies (Production)

For the complete ML stack with FinBERT, spaCy, and FAISS:

```bash
pip install -r requirements.txt
```

This includes PyTorch (~2GB), Transformers, sentence-transformers, and spaCy.

---

## 📜 License

Hackathon prototype — MIT License.
