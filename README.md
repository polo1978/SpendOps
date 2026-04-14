# SpendOps

**Agentic Department Budget Intelligence Platform**

SpendOps turns contract and budget data into a live, AI-powered spend intelligence dashboard. A multi-agent pipeline detects renewal risk, flags anomalies, recommends consolidations, and forecasts end-of-year spend — all served through a reactive local web app.

Built as a working demo for IT/OT spend management consulting. Company: NextChems (fictional). Data: realistic mock data with embedded problems.

---

## What It Does

| Tab | What you see |
|-----|--------------|
| **Dashboard** | KPI cards (budget / actual YTD / forecast EOY / variance), renewal risk register, anomaly flags by severity, consolidation recommendations, AI-generated narrative brief, spend-by-category chart |
| **Data → Contracts** | Editable contract registry — add, edit, delete, import CSV; changes reflect in the risk register immediately |
| **Data → Budget Lines** | Personnel salaries, hardware, outsourcing, and other non-contract budget lines — editable inline with plan-vs-actual progress bars |
| **SpendOps Analyst** | Natural language chat grounded in your current spend data |

---

## Prerequisites

- Python 3.9+
- An [OpenRouter](https://openrouter.ai) API key (free tier works — models used are cheap)
- No database server needed — SQLite only

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/pauloalzate/SpendOps.git
cd SpendOps/workspace-spendops
pip install -r requirements.txt
```

### 2. Configure your API key

```bash
cp .env.example .env
```

Open `.env` and set your key:

```
OPENROUTER_API_KEY=sk-or-v1-...
```

Get a key at [openrouter.ai](https://openrouter.ai) — no credit card required for the free tier.

### 3. Create and seed the database

```bash
python scripts/init_db.py --db ./spendops.db
sqlite3 spendops.db < mock_data.sql
```

### 4. Start the web app

```bash
uvicorn app:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000).

The dashboard loads with the last pipeline output. To run a fresh AI analysis, click **Refresh Analysis** in the Data tab — it runs all 6 agents and streams progress live.

---

## Running on Windows (PC or Server)

Windows requires a few small differences from the standard quick start above.

### 1. Download the code (no Git required)

Go to the repository on GitHub, click the green **Code** button, and select **Download ZIP**.  
Extract the ZIP anywhere — e.g. `C:\Users\YourName\Documents\SpendOps`.

> If you prefer Git: open **Control Panel → Credential Manager → Windows Credentials**, delete any stored `github.com` entry, then run `git clone https://github.com/polo1978/SpendOps.git`. For a public repo no credentials are needed, but stale cached tokens cause failures.

### 2. Open a Command Prompt in the right folder

```
cd "C:\path\to\SpendOps-main\workspace-spendops"
```

### 3. Install dependencies

```
pip install -r requirements.txt
```

### 4. Configure your API key

```
copy .env.example .env
```

Open `.env` in Notepad and set your key:

```
OPENROUTER_API_KEY=sk-or-v1-...
```

### 5. Create and seed the database

`sqlite3` is not installed on Windows by default. Use this Python one-liner instead — paste it as a single line:

```
python scripts/init_db.py --db ./spendops.db
```

```
python -c "import sqlite3; conn = sqlite3.connect('spendops.db'); conn.executescript(open('mock_data.sql').read()); conn.commit(); conn.close(); print('Done')"
```

### 6. Start the app

```
uvicorn app:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000).

### Running the pipeline manually on Windows

Use semicolons instead of backslash line continuations:

```
python scripts/run_pipeline.py --department "IT/OT" --cycle FY2026 --db ./spendops.db --output-dir ./outputs/
```

### Common Windows issues

| Error | Cause | Fix |
|-------|-------|-----|
| `UnicodeDecodeError: 'charmap' codec can't decode` | Windows reads files as cp1252 by default | Already fixed in the current codebase — make sure you have the latest version |
| `git clone` asking for credentials and failing | Stale token in Windows Credential Manager | Delete the stored `github.com` entry in Credential Manager, or just download the ZIP |
| `sqlite3` not found | SQLite CLI is not bundled with Windows Python | Use the Python one-liner in step 5 above |
| `uvicorn` not found | pip install didn't add scripts to PATH | Try `python -m uvicorn app:app --reload --port 8000` |
| Port 8000 already in use | Another process is using 8000 | Change to any free port: `--port 8001` |

---

## Running the Pipeline Manually

The pipeline can also be run from the command line (useful for cron jobs or CI):

```bash
python scripts/run_pipeline.py \
  --department "IT/OT" \
  --cycle FY2026 \
  --db ./spendops.db \
  --output-dir ./outputs/
```

This runs 6 agents in sequence and writes JSON outputs to `./outputs/`. The web app reads those files via `/api/results`.

---

## Project Structure

```
SpendOps/
├── workspace-spendops/
│   ├── app.py                  # FastAPI web server — all API endpoints
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example            # Environment variable template
│   ├── mock_data.sql           # Demo data seed (NextChems IT/OT FY2026)
│   ├── scripts/
│   │   ├── init_db.py          # Create SQLite schema
│   │   ├── read_db.py          # Export DB tables to JSON
│   │   ├── calc_forecast.py    # Pre-compute EOY forecasts (no AI, pure math)
│   │   ├── run_agent.py        # Run a single AI agent
│   │   ├── run_pipeline.py     # Orchestrate the full 6-agent pipeline
│   │   └── infer_schema.py     # Infer schema from uploaded CSV/Excel
│   └── templates/
│       └── dashboard.html      # Reactive single-page app (served by FastAPI)
├── vercel.json                 # Vercel deployment config
├── .gitignore
└── README.md
```

Generated at runtime (git-ignored):
```
workspace-spendops/
├── spendops.db                 # SQLite database
├── data/                       # JSON exports from read_db.py
└── outputs/                    # Agent JSON outputs + forecast_summary.json
```

---

## AI Agent Pipeline

Six specialist agents run in sequence. Each calls OpenRouter and writes a JSON file to `outputs/`:

| Agent | Model | Output |
|-------|-------|--------|
| `renewal_risk` | Gemini 2.0 Flash | Renewals expiring in 30/60/90 days, missing owners |
| `run_rate_forecast` | Gemini 2.0 Flash | EOY spend projection per category |
| `anomaly_detect` | Gemini 2.0 Flash | Spend anomalies vs plan, ranked by dollar impact |
| `consolidation_suggest` | Claude 3.5 Haiku | Vendor overlap + consolidation opportunities |
| `orchestrator` | Claude 3.5 Haiku | Master brief merging all specialist outputs |
| `narrative_brief` | Claude 3.5 Haiku | Numbers-first executive summary with specific dollar amounts |

**Forecasting is pre-computed** — `calc_forecast.py` runs before the agents and produces `forecast_summary.json` using rolling averages and subscription renewal overlays. Agents receive the computed numbers and explain them; they do not recalculate.

### Changing models

Override in `.env`:

```
OPENROUTER_MODEL_FAST=google/gemini-2.0-flash-001   # data-parsing agents
OPENROUTER_MODEL_SMART=anthropic/claude-3-5-haiku   # reasoning agents
```

Or per-agent in `scripts/run_agent.py` → `AGENT_MODELS` dict.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Yes | OpenRouter API key |
| `OPENROUTER_MODEL_FAST` | No | Model for data-parsing agents (default: `google/gemini-2.0-flash-001`) |
| `OPENROUTER_MODEL_SMART` | No | Model for reasoning agents (default: `anthropic/claude-3-5-haiku`) |
| `SPENDOPS_AUTH_PASSWORD` | No | Enables HTTP Basic Auth — set on Vercel to protect public deployments |

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Dashboard HTML |
| `GET` | `/api/contracts` | List all contracts |
| `POST` | `/api/contracts` | Add contract |
| `PUT` | `/api/contracts/{id}` | Update contract field(s) |
| `DELETE` | `/api/contracts/{id}` | Delete contract |
| `GET` | `/api/vendors` | List all vendors |
| `GET` | `/api/budget-lines` | Non-subscription budget lines (Personnel, Hardware, etc.) |
| `POST` | `/api/budget-lines` | Add budget line |
| `PUT` | `/api/budget-lines/{id}` | Update description or plan annual |
| `DELETE` | `/api/budget-lines/{id}` | Delete budget line and its monthly data |
| `GET` | `/api/budget-settings` | Approved budget total |
| `PUT` | `/api/budget-settings` | Update approved budget (scales all planned_amounts) |
| `GET` | `/api/results` | Latest agent JSON outputs merged |
| `POST` | `/api/run-analysis` | Trigger full pipeline |
| `GET` | `/api/analysis-stream` | SSE progress stream (per-agent steps) |
| `GET` | `/api/analysis-status` | Polling fallback for pipeline status |
| `POST` | `/api/analyst` | SpendOps Analyst chat |
| `POST` | `/api/upload-data` | Upload CSV/Excel for schema inference |

---

## Demo Data Story

The mock data is designed to tell a specific story for NextChems IT/OT FY2026:

- **ServiceNow ITSM** — past due, no owner (renewal risk)
- **CrowdStrike Falcon** — recent renewal, previously flagged as overdue with no owner
- **ManageEngine + SolarWinds** — overlapping network monitoring tools (consolidation candidate)
- **Tenable OT + Claroty xDome** — OT security overlap worth evaluating
- **AWS Cloud** — trending over budget at EOY (anomaly)
- **Personnel** — 5 salary lines totaling ~$270K planned

Run `Refresh Analysis` to see the AI identify all of these from the raw data.

---

## Vercel Deployment

> Note: Vercel's serverless runtime uses an ephemeral filesystem — the SQLite DB resets on each deployment. For a persistent Vercel deployment, point `DATABASE_URL` to a [Turso](https://turso.tech) database (SQLite-compatible, free tier).

1. Push repo to GitHub
2. Import at [vercel.com](https://vercel.com) → select `workspace-spendops/app.py` as entry point
3. Set environment variables in Vercel dashboard:
   - `OPENROUTER_API_KEY`
   - `SPENDOPS_AUTH_PASSWORD` (recommended — username will be `spendops`)
4. Deploy

The `vercel.json` at the repo root handles routing.

---

## Running on a Remote Server (Linux VPS)

```bash
# Install deps
pip install -r requirements.txt

# Set up DB
python scripts/init_db.py --db ./spendops.db
sqlite3 spendops.db < mock_data.sql

# Copy and configure .env
cp .env.example .env && nano .env

# Run with gunicorn (production)
pip install gunicorn
gunicorn app:app -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Or keep it simple with uvicorn
uvicorn app:app --host 0.0.0.0 --port 8000
```

Use nginx as a reverse proxy and Let's Encrypt for HTTPS if exposing publicly. Set `SPENDOPS_AUTH_PASSWORD` to require a password.

---

## Tech Stack

- **Python / FastAPI** — API server + pipeline orchestration
- **SQLite** — local database, zero setup
- **OpenRouter** — AI API router (Gemini Flash + Claude Haiku)
- **Chart.js** — spend-by-category chart
- **Vanilla JS** — no framework, SSE for live pipeline streaming
- **Fira Sans / Fira Code** — typography
