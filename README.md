# 💰 FinanceGPT — AI-Powered CFO Audit Platform

> Production-grade financial audit platform powered by Anthropic Claude. Detect anomalies, generate CFO-grade audit reports, and chat with your financial data in plain language.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        PRODUCTION STACK                      │
├──────────────┬──────────────┬──────────────┬────────────────┤
│   Nginx      │  React+Vite  │  FastAPI     │  PostgreSQL    │
│  (Reverse    │  (TypeScript │  (Python 3.12│  (16-alpine)   │
│   Proxy)     │   Tailwind)  │  Async)      │                │
├──────────────┴──────────────┴──────────────┴────────────────┤
│                     Anthropic Claude API                     │
│         (claude-opus-4-6 — Audit Engine & Q&A)              │
├─────────────────────────────────────────────────────────────┤
│  Redis (Background Tasks)  │  Docker Compose + GitHub Actions│
└─────────────────────────────────────────────────────────────┘
```

### System Flow

```
User Uploads File (CSV/Excel/PDF)
    │
    ▼
Document Parser (pandas / pdfplumber)
    │
    ▼
AI Extraction Engine (Claude) ──► KPIs Extracted
    │
    ▼
Anomaly Detector (Claude) ──────► Anomalies Flagged + Saved
    │
    ▼
CFO Audit Report Generator
    │
    ▼
Risk Score + Executive Summary + Recommendations
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **AI Engine** | Anthropic Claude (claude-opus-4-6) |
| **Backend API** | Python 3.12, FastAPI (async), SQLAlchemy 2.0 |
| **Database** | PostgreSQL 16 (asyncpg) |
| **Cache/Queue** | Redis 7 |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS |
| **Auth** | JWT (python-jose), bcrypt (passlib) |
| **Doc Parsing** | pandas, pdfplumber, openpyxl |
| **Integrations** | QuickBooks Online API, Xero API (OAuth 2.0) |
| **Containerization** | Docker, Docker Compose |
| **Reverse Proxy** | Nginx (rate limiting, SSL, gzip) |
| **CI/CD** | GitHub Actions → SSH deploy |

---

## Quick Start (One Command)

```bash
# 1. Clone and configure
git clone https://github.com/yourorg/financegpt.git
cd financegpt
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY and SECRET_KEY

# 2. Launch everything
docker-compose up -d

# 3. Open the app
open http://localhost
```

**That's it.** The app is running on port 80 with:
- React dashboard at `http://localhost`
- FastAPI docs at `http://localhost/api/redoc`
- PostgreSQL on port 5432
- Redis on port 6379

---

## Local Development

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment
export ANTHROPIC_API_KEY="sk-ant-api03-..."
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/financegpt"
export SECRET_KEY="dev-secret-key"

# Start DB only
docker-compose up -d postgres redis

# Run migrations (first time)
alembic upgrade head

# Start API with hot reload
uvicorn app.main:app --reload --port 8000
```

API available at `http://localhost:8000`  
Interactive docs at `http://localhost:8000/api/redoc`

### Frontend

```bash
cd frontend
npm install

# Configure API URL
echo "VITE_API_URL=http://localhost:8000/api" > .env.local

# Start dev server
npm run dev
```

Frontend at `http://localhost:5173`

---

## API Reference

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login → JWT tokens |
| GET | `/api/auth/me` | Current user info |
| POST | `/api/auth/refresh` | Refresh access token |

### Documents
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/documents/upload` | Upload CSV/Excel/PDF |
| GET | `/api/documents` | List all documents |
| GET | `/api/documents/{id}` | Get document details |
| DELETE | `/api/documents/{id}` | Delete document |

### Audit Engine
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/audit/reports` | Generate CFO audit report |
| GET | `/api/audit/reports` | List all reports |
| GET | `/api/audit/reports/{id}` | Get full report |
| GET | `/api/audit/anomalies` | List anomalies (filterable) |
| PATCH | `/api/audit/anomalies/{id}` | Update anomaly status |
| POST | `/api/audit/chat` | Chat with financial data |
| GET | `/api/audit/dashboard` | Dashboard metrics |

### Integrations
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/integrations` | List connected integrations |
| GET | `/api/integrations/quickbooks/authorize` | Start QB OAuth |
| GET | `/api/integrations/quickbooks/sync` | Sync QB data |
| GET | `/api/integrations/xero/authorize` | Start Xero OAuth |
| DELETE | `/api/integrations/{id}` | Disconnect integration |

---

## User Roles & Permissions

| Role | Upload Docs | Generate Reports | Resolve Anomalies | Manage Integrations | Admin |
|------|-------------|-----------------|-------------------|--------------------|----|
| **super_admin** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **cfo** | ✅ | ✅ | ✅ | ✅ | ❌ |
| **auditor** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **analyst** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **viewer** | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## CFO Audit Report — What You Get

Every generated report includes:

**Health Scores (0-100)**
- Overall Financial Health Score
- Liquidity Score (current ratio, quick ratio)
- Profitability Score (margins, ROE, ROA)
- Solvency Score (debt-to-equity, coverage ratios)
- Efficiency Score (DSO, inventory turnover)

**Risk Matrix**
- Financial Reporting Risk
- Liquidity Risk
- Operational Risk
- Compliance Risk
- Fraud Risk
- Market Risk

**AI-Detected Anomalies**
- Unusual variances (>2σ from expected)
- Benford's Law violations (round number concentration)
- Year-end spikes
- Ratio outliers vs. industry benchmarks
- Missing/unreconciled items
- Policy breaches

**Recommendations**
- Immediate actions (critical findings)
- Short-term improvements (30-90 days)
- Long-term strategic initiatives

**KPIs Extracted**
Revenue, Gross Profit, EBITDA, Net Income, all margin percentages, all liquidity/solvency/efficiency ratios — automatically extracted from your uploaded documents.

---

## Production Deployment

### Requirements
- Ubuntu 22.04 server (2GB+ RAM)
- Docker & Docker Compose installed
- Domain with DNS pointed to server
- SSL certificate (Let's Encrypt recommended)

### Deploy

```bash
# On your server
git clone https://github.com/yourorg/financegpt.git /opt/financegpt
cd /opt/financegpt
cp .env.example .env
nano .env  # Fill in all values

# Generate a strong secret key
python3 -c "import secrets; print(secrets.token_hex(64))"

# Start production stack
docker-compose up -d

# Run database migrations
docker-compose exec backend alembic upgrade head

# Check logs
docker-compose logs -f backend
```

### SSL (Let's Encrypt)
```bash
apt install certbot
certbot certonly --standalone -d financegpt.yourdomain.com
# Certs saved to /etc/letsencrypt/live/...
# Copy to nginx/ssl/ and update nginx.conf
```

### GitHub Actions CI/CD
Set these secrets in your GitHub repo:
- `ANTHROPIC_API_KEY` — your Claude API key
- `PROD_HOST` — production server IP
- `PROD_USER` — SSH username
- `PROD_SSH_KEY` — SSH private key

Push to `main` branch → automated test → build Docker images → deploy to production.

---

## Adding QuickBooks Integration

1. Create app at https://developer.intuit.com
2. Set redirect URI: `https://yourdomain.com/api/integrations/quickbooks/callback`
3. Add `QB_CLIENT_ID` and `QB_CLIENT_SECRET` to `.env`
4. Set `QB_ENVIRONMENT=production`
5. Users connect via Settings → Integrations → QuickBooks

---

## Project Structure

```
financegpt/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + middleware
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   ├── database.py          # Async SQLAlchemy setup
│   │   ├── models/              # SQLAlchemy ORM models
│   │   │   ├── user.py
│   │   │   ├── company.py
│   │   │   ├── document.py
│   │   │   ├── audit_report.py
│   │   │   ├── anomaly.py
│   │   │   └── integration.py
│   │   ├── routers/             # API endpoints
│   │   │   ├── auth.py
│   │   │   ├── documents.py
│   │   │   ├── audit.py
│   │   │   └── integrations.py
│   │   ├── services/            # Business logic
│   │   │   ├── ai_audit_engine.py   # Claude-powered audit
│   │   │   └── document_parser.py   # File parsing
│   │   ├── schemas/             # Pydantic schemas
│   │   └── core/
│   │       └── security.py      # JWT, RBAC
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Root routing
│   │   ├── pages/               # Full page components
│   │   │   ├── Dashboard.tsx    # CFO metrics overview
│   │   │   ├── Documents.tsx    # File upload & management
│   │   │   ├── AuditReports.tsx # Report generation & viewer
│   │   │   ├── Anomalies.tsx    # Anomaly management
│   │   │   ├── Chat.tsx         # Financial Q&A
│   │   │   ├── Integrations.tsx # QB & Xero connections
│   │   │   └── Login.tsx
│   │   ├── components/          # Reusable UI components
│   │   ├── services/api.ts      # Axios client + interceptors
│   │   ├── hooks/useAuth.ts     # Zustand auth store
│   │   └── types/index.ts       # TypeScript types
│   ├── package.json
│   └── Dockerfile
├── nginx/
│   └── nginx.conf               # Rate limiting, SSL, proxy
├── .github/
│   └── workflows/ci.yml         # CI/CD pipeline
├── scripts/
│   └── init.sql                 # DB initialization
├── docker-compose.yml           # Full stack orchestration
├── .env.example                 # Configuration template
└── README.md
```

---

## License

MIT License — built for production use.

---

*Built with Anthropic Claude, FastAPI, React, and PostgreSQL.*
