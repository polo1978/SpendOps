# SpendOps — Claude Code Project Brief

## What This Is

SpendOps is a local operational spend management platform built as a demo. The goal is to show that an independent consultant can build a functioning AI-powered spend analysis tool for a IT/OT department, end to end, without a cloud backend.

This is a **demo-first project**. The data is fictional. The company is fictional. The output needs to look real enough to showcase and prove the concept to potential clients.

---

## The Story Behind It

Paulo Alzate (me) is building an independent consulting practice focused on operational spend optimization for life sciences and manufacturing companies. SpendOps is the proof-of-concept that anchors the portfolio. The demo scenario:

- **Company:** NextChems (fictional)
- **Department:** IT/OT
- **Budget cycle:** FY2026
- **Budget:** $905,692
- **Actual YTD:** $233,499
- **Forecast EOY:** $1,066,746
- **Variance:** +$161,054 (over budget)

The demo story has four concrete problems embedded in the data:
1. **Clarody xDome** renewal in 9 days, no owner assigned
2. **CrowdStrike** renewal in 18 days, no owner assigned
3. **ServiceNow** has a VACANT owner field
4. **AWS** is trending +$60K over budget at EOY
5. **SolarWinds + ManageEngine** overlap in functionality, consolidation candidate
6. **IBM Maximo** underutilized, cancellation candidate

---

## What Was Built So Far

### Infrastructure (complete)
- SQLite database `spendops.db` with mock data loaded
- Mock data SQL file: `mock_data.sql`
- Python scripts:
  - `scripts/init_db.py` — creates and seeds the database
  - `scripts/read_db.py` — exports data to JSON
  - `scripts/calc_forecast.py` — runs EOY forecast pre-computation, produces `forecast_summary.json`
  - `scripts/run_agent.py` — calls LM Studio with a prompt and returns structured output
  - `scripts/run_pipeline.py` — orchestrates all 7 agents in sequence

### Agent Pipeline (complete, runs via PowerShell)
Seven sequential agents, each called via `run_agent.py`:
1. `renewal_risk` — flags contracts expiring within 30 days, flags missing owners
2. `run_rate_forecast` — projects EOY spend per category using YTD actuals
3. `anomaly_detect` — identifies spend anomalies vs budget
4. `consolidation_suggest` — recommends vendor consolidation opportunities
5. `orchestrator` — synthesizes the four above into a master JSON
6. `narrative_brief` — writes a plain-English executive summary
7. `html_dashboard_builder` — produces an HTML dashboard from all outputs

---

## The End Goal

### Minimum Viable Demo
A single command or prompt that:
1. Reads the SQLite database
2. Runs the 7-agent pipeline
3. Produces a polished fucntional dashboard (GUI)

### What "Good Enough" Means for the Dashboard
- Dark theme, executive aesthetic, professional typography
- Budget summary cards (total budget, actual YTD, forecast EOY, variance)
- Renewal risk table with urgency indicators (red for <14 days, amber for <30 days)
- Spend by category chart
- Anomaly flags section
- Consolidation recommendations section
- AI-generated narrative brief at the top
- Company: NextChems | Department: IT/OT | Cycle: FY2026 | Generated: [date]

### Stretch Goal
A simple web UI (local, no cloud) where Paulo can:
- Select department and budget cycle
- Click "Run Analysis"
- See the dashboard render in the browser
- Export as PDF

---

## Tech Stack

- **Python**
- **SQLite** via Python's built-in `sqlite3`
- **AI API** help me find the right one either Claude, Gemini, or OpenAI
- **HTML/CSS/JS** for the dashboard output
- **Claude Code** as the agentic runner

### MCP Tools Available in Claude Code
- **Nano Banana 2 MCP** — AI image generation (Gemini 3.1 Flash) right inside Claude Code
- **UI UX Pro Max MCP** — Design intelligence: 97 color palettes, 57 font pairings, 50 styles, 99 UX guidelines
- **21st.dev Magic MCP** — Generates polished React UI components from natural language

Use these MCPs aggressively for the dashboard design. The visual quality of the HTML output is a primary deliverable. This is a portfolio piece.

---

## Immediate Next Steps for Claude Code

1. **Verify the database** — confirm `spendops.db` exists and has data:
2. **Run the pipeline** — confirm all 7 agents complete:
3. **Evaluate the current dashboard** — open `outputs\dashboard.html` in a browser. The current quality is poor (produced by a weak local model). This needs to be completely rebuilt.
4. **Rebuild the dashboard** — use the JSON outputs in `outputs\` plus the design MCPs to produce a production-quality HTML dashboard that tells the Nexagen IT/OT spend story clearly and visually.
5. **Iterate on the narrative** — the `narrative_brief` agent output is the text content that anchors the dashboard. If the AI-generated narrative is weak, rewrite the `narrative_brief` agent prompt to produce something sharper.

---

## Design Direction for the Dashboard

This is a IT/OT spend report. The aesthetic should feel like:
- Enterprise analytics, not startup SaaS
- Confident, data-dense but not overwhelming
- Dark background (#0f1117 or similar), bright accent (electric blue or teal)
- Monospace or technical font for numbers
- Clean sans-serif for body
- No gradients for gradients' sake. Purpose-driven visual hierarchy.

The person viewing this is a VP of Operations or a CFO. They need to see the problem in 10 seconds and the recommended actions in 30 seconds.

---

## Files to Know About

| File | Purpose |
|------|---------|
| `spendops.db` | Source of truth. All data lives here. |
| `mock_data.sql` | SQL to recreate the database if needed |
| `scripts/run_pipeline.py` | Main entry point. Run this to produce all outputs. |
| `outputs/html_dashboard_builder.html` | Current (poor quality) dashboard. Replace this. |
| `outputs/orchestratorjson` | Master JSON from the orchestrator agent |
| `outputs/narrative_brief.json` | AI-generated narrative text |
| `outputs/renewal_risk.json` | Renewal risk flags |
| `outputs/forecast_summary.json` | Pre-computed forecast numbers |
| `AGENTS.md` | Agent operating instructions (originally for OpenClaw, reusable as system prompt context) |
| `SOUL.md` | Agent persona (SpendOps analyst voice) |

---

## Notes on the Data

The mock data was designed to tell a specific story. Do not change the core numbers. The story is:
- NextChems is over budget in FY2026
- Two critical renewals have no owner (real risk, demo-worthy)
- AWS is the biggest overspend driver
- There are two consolidation opportunities that together save ~$40K/year

If any script fails to find the database or JSON outputs, re-run `init_db.py` then `read_db.py` before running the full pipeline.
