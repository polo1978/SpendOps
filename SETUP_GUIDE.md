# SpendOps on OpenClaw — Complete Setup Guide

**Audience:** You installed OpenClaw but have not configured anything yet.  
**Goal:** Get SpendOps running end-to-end: database → agents → LM Studio → HTML dashboard.  
**Platform:** Windows with WSL2 (where OpenClaw runs) + LM Studio running natively on Windows.

---

## Before you start — what you need

| Thing | Status needed |
|-------|--------------|
| OpenClaw installed | Done (you said so) |
| WSL2 installed and working | Required — OpenClaw runs inside WSL2 on Windows |
| Python 3.10+ in WSL2 | Required — check with `python3 --version` |
| LM Studio installed on Windows | Required — download from lmstudio.ai |
| Qwen model downloaded in LM Studio | Required — download Qwen 2.5 7B or larger from LM Studio's model browser |

---

## Phase 1. Finish OpenClaw onboarding (if you skipped it)

### Step 1.1 — Open your WSL2 terminal

On Windows: Start menu → search "WSL" or "Ubuntu" → open it.  
You will see a Linux command prompt.

### Step 1.2 — Run the onboarding wizard (if not done yet)

```bash
openclaw onboard --install-daemon
```

The wizard will walk you through:
- Setting up the Gateway (the background service)
- Choosing a model provider (pick "Local / LM Studio" when asked)
- Creating the workspace folder

If you already ran onboard before, skip this step.

### Step 1.3 — Check that the Gateway is running

```bash
openclaw gateway status
```

You should see something like: `Gateway running on port 18789`.  
If it says stopped, start it with: `openclaw gateway start`

### Step 1.4 — Run the doctor check

```bash
openclaw doctor
```

This tells you if anything is misconfigured. Fix anything it flags before continuing.

---

## Phase 2. Connect OpenClaw to LM Studio

### Step 2.1 — Start LM Studio server on Windows

1. Open LM Studio on Windows.
2. Click the **"Local Server"** tab (server icon on the left sidebar).
3. Select your downloaded Qwen model from the dropdown.
4. Click **"Start Server"**.
5. You should see: `Server running on port 1234`.

### Step 2.2 — Find your WSL2 host IP (Windows-specific issue)

From WSL2, run:

```bash
cat /etc/resolv.conf | grep nameserver
```

You will see something like: `nameserver 172.28.192.1`  
That IP is how WSL2 reaches your Windows host (where LM Studio runs).

Test it:

```bash
curl http://172.28.192.1:1234/v1/models
```

If you get a JSON response with model names, you are connected.  
If `127.0.0.1:1234` also works, use that — it is simpler.  
Use whichever IP works. You will need it in the next step.

### Step 2.3 — Edit your OpenClaw config to point at LM Studio

Open the config file in a text editor:

```bash
nano ~/.openclaw/openclaw.json
```

Find the `"models"` section (or add it if missing). Merge in this block, replacing `172.28.192.1` with your actual WSL2 host IP from step 2.2:

```json
"models": {
  "providers": {
    "lmstudio": {
      "baseUrl": "http://172.28.192.1:1234/v1",
      "apiKey": "lm-studio",
      "api": "openai-responses",
      "models": [
        {
          "id": "qwen2.5-72b-instruct",
          "name": "Qwen 2.5",
          "input": ["text"],
          "cost": { "input": 0, "output": 0 },
          "contextWindow": 8192,
          "maxTokens": 4096
        }
      ]
    }
  }
},
"agents": {
  "defaults": {
    "model": {
      "primary": "lmstudio/qwen2.5-72b-instruct"
    }
  }
}
```

Save and close (in nano: Ctrl+O, Enter, Ctrl+X).

> **Important:** The `id` field must exactly match the model name shown in LM Studio. Open LM Studio → Local Server → check the model name. Copy it exactly and paste it into the `id` field above.

### Step 2.4 — Restart the Gateway

```bash
openclaw gateway restart
```

### Step 2.5 — Test that OpenClaw reaches LM Studio

Open the OpenClaw web interface at: `http://localhost:18789`  
Send a test message: `"Say hello"`  
If you get a response, the model connection is working.

---

## Phase 3. Set up the SpendOps workspace

### Step 3.1 — Go to your workspace folder

```bash
cd ~/.openclaw/workspace
ls
```

You will see files like `AGENTS.md`, `SOUL.md`, `IDENTITY.md`, `USER.md` already there from onboarding.

### Step 3.2 — Copy the SpendOps workspace files

You downloaded a zip or folder with these files. Copy them in:

```bash
# Replace /path/to/your/downloaded/files with where you saved the files
cp /path/to/spendops_workspace_files/AGENTS.md ~/.openclaw/workspace/AGENTS.md
cp /path/to/spendops_workspace_files/SOUL.md ~/.openclaw/workspace/SOUL.md
cp /path/to/spendops_workspace_files/USER.md ~/.openclaw/workspace/USER.md
cp /path/to/spendops_workspace_files/HEARTBEAT.md ~/.openclaw/workspace/HEARTBEAT.md
cp /path/to/spendops_workspace_files/TOOLS.md ~/.openclaw/workspace/TOOLS.md
```

> If you already have AGENTS.md, SOUL.md etc. from onboarding and want to keep your existing persona, you can skip those and only copy HEARTBEAT.md and TOOLS.md. Then manually add the SpendOps rules from AGENTS.md into your existing file.

### Step 3.3 — Copy the skills

```bash
# Create the skills directory if it does not exist
mkdir -p ~/.openclaw/workspace/skills

# Copy each SpendOps skill folder
cp -r /path/to/skills/spendops-orchestrator ~/.openclaw/workspace/skills/
cp -r /path/to/skills/spendops-run-calc ~/.openclaw/workspace/skills/
cp -r /path/to/skills/spendops-read-db ~/.openclaw/workspace/skills/
```

Verify:

```bash
ls ~/.openclaw/workspace/skills/
# Should show: spendops-orchestrator  spendops-run-calc  spendops-read-db
```

### Step 3.4 — Copy the Python scripts

```bash
mkdir -p ~/.openclaw/workspace/scripts
cp /path/to/scripts/init_db.py ~/.openclaw/workspace/scripts/
cp /path/to/scripts/read_db.py ~/.openclaw/workspace/scripts/
cp /path/to/scripts/calc_forecast.py ~/.openclaw/workspace/scripts/
cp /path/to/scripts/run_agent.py ~/.openclaw/workspace/scripts/
cp /path/to/scripts/run_pipeline.py ~/.openclaw/workspace/scripts/
```

### Step 3.5 — Create outputs and data folders

```bash
mkdir -p ~/.openclaw/workspace/outputs
mkdir -p ~/.openclaw/workspace/data
```

### Step 3.6 — Update your USER.md with your real details

```bash
nano ~/.openclaw/workspace/USER.md
```

Replace the placeholder lines with your name, department, and fiscal year.

---

## Phase 4. Initialize the database

### Step 4.1 — Go to the workspace folder

```bash
cd ~/.openclaw/workspace
```

### Step 4.2 — Run the database initializer

```bash
python3 scripts/init_db.py --db ./spendops.db
```

You should see:
```
Database initialized: ./spendops.db
Categories seeded: Hardware, Software & Licenses, Personnel, ...
```

### Step 4.3 — Verify the database

```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('./spendops.db')
tables = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()
print('Tables:', [t[0] for t in tables])
"
```

You should see all 8 tables listed.

---

## Phase 5. Add your actual data

The database is empty. You need to add your departments, subscriptions, and budget data.

### Option A — Let the agent do it (recommended)

Restart the gateway, then send this message in the OpenClaw web chat:

```
I need to set up SpendOps data. I have a list of my SaaS subscriptions and budget lines. Can you help me insert them into the database at ./spendops.db?
```

The agent will guide you through inserting data. You can paste CSV rows, or describe your subscriptions and it will write the SQL.

### Option B — Insert manually via SQL

```bash
# Open the database
sqlite3 ./spendops.db

# Example: add a department
INSERT INTO departments (name) VALUES ('IT');

# Add a budget cycle
INSERT INTO budget_cycles (name, start_date, end_date) VALUES ('FY2026', '2026-01-01', '2026-12-31');

# Add a vendor
INSERT INTO vendors (name, website) VALUES ('GitHub', 'github.com');

# Add a subscription
INSERT INTO subscriptions (department_id, vendor_id, product_name, owner_name, renewal_date, auto_renew, annual_cost)
VALUES (1, 1, 'GitHub Team', 'Jane Smith', '2026-09-01', 1, 4800.00);

# Exit sqlite3
.quit
```

---

## Phase 6. Run SpendOps for the first time

### Step 6.1 — Verify LM Studio is running

```bash
curl http://172.28.192.1:1234/v1/models
# Should return model info. If it fails, start the server in LM Studio first.
```

### Step 6.2 — Run the full pipeline

```bash
cd ~/.openclaw/workspace

python3 scripts/run_pipeline.py \
  --department "IT" \
  --cycle "FY2026" \
  --db ./spendops.db \
  --output-dir ./outputs/
```

This will take several minutes — each agent calls LM Studio in sequence.  
You will see progress printed for each step.

### Step 6.3 — Open the dashboard

When the pipeline finishes, it will print the path to the HTML file.  
Copy that path and open it in your Windows browser:

```bash
# In WSL2, the workspace is accessible from Windows at:
# \\wsl$\Ubuntu\home\YOUR_USERNAME\.openclaw\workspace\outputs\
# Drag the HTML file into Chrome or Edge.
```

Or open it directly:
```bash
# On WSL2 with wslview installed:
wslview ./outputs/html_dashboard_builder.html
```

---

## Phase 7. Use it via OpenClaw chat (ongoing)

Once everything is set up, you can trigger the pipeline by chatting with the agent.

Open `http://localhost:18789` in your browser, or connect a messaging channel (Telegram, Discord, etc.) if you set one up during onboarding.

### Sample commands to try:

**Full brief:**
```
Run SpendOps brief for IT, FY2026
```

**Renewals only:**
```
Show me all IT subscriptions renewing in the next 90 days
```

**Forecast only:**
```
What is the IT department tracking vs budget for FY2026?
```

**Dashboard refresh:**
```
Rebuild the dashboard for IT FY2026
```

**Add a subscription:**
```
Add a new subscription: vendor Zoom, product Zoom Business, owner Sarah Lee, annual cost $2400, renewal date 2026-11-01, department IT
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `curl http://172.x.x.x:1234/v1/models` fails | Start the server inside LM Studio. Make sure "Start Server" is clicked, not just a model loaded. |
| Agent returns garbled or partial JSON | Qwen with less than 8GB VRAM may truncate. Reduce context window in LM Studio settings, or use a smaller model. |
| `openclaw gateway status` says stopped | Run `openclaw gateway start` |
| Skills not loading | Check: `ls ~/.openclaw/workspace/skills/spendops-orchestrator/` — SKILL.md must be there. Then restart gateway. |
| Pipeline runs but dashboard is empty | Check `outputs/orchestrator.json` — if it contains an error field, the Orchestrator failed. Run individual agents to find which one broke. |
| WSL2 can't reach LM Studio | In LM Studio → Local Server settings → set "Listen on" to `0.0.0.0` instead of `127.0.0.1`, then restart the server. |
| `python3: command not found` | In WSL2: `sudo apt update && sudo apt install python3` |

---

## Files reference

```
~/.openclaw/openclaw.json           ← Gateway + model config (edit this)
~/.openclaw/workspace/
├── AGENTS.md                       ← Agent operating instructions
├── SOUL.md                         ← Agent persona
├── USER.md                         ← Your profile (edit this)
├── HEARTBEAT.md                    ← Periodic check rules
├── TOOLS.md                        ← Local paths and tools
├── spendops.db                     ← Your actual financial data
├── scripts/
│   ├── init_db.py                  ← Run once on setup
│   ├── read_db.py                  ← Exports data to JSON
│   ├── calc_forecast.py            ← Pre-computes rolling average forecast
│   ├── run_agent.py                ← Calls LM Studio for one agent
│   └── run_pipeline.py             ← Runs all agents in order
├── skills/
│   ├── spendops-orchestrator/SKILL.md
│   ├── spendops-run-calc/SKILL.md
│   └── spendops-read-db/SKILL.md
├── data/                           ← JSON exports from DB (auto-generated)
└── outputs/                        ← Agent results + dashboard HTML
```

---

*End of setup guide — SpendOps v0.2*
