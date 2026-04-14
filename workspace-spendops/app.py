#!/usr/bin/env python3
"""
SpendOps - FastAPI Web Application
Serves the live dashboard and exposes APIs for contract CRUD, pipeline execution,
SpendOps Analyst chat, and data upload with schema inference.

Run: uvicorn app:app --reload --port 8000
"""

import asyncio
import json
import os
import sqlite3
import subprocess
import sys
import time
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Depends
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Paths — Vercel-aware
# Vercel's deployment filesystem is read-only; only /tmp is writable.
# We detect Vercel via the VERCEL env var and redirect all mutable paths there.
# On first cold start we copy the pre-seeded DB from the deployment bundle.
# ---------------------------------------------------------------------------
import shutil

WORKSPACE = Path(__file__).parent
TEMPLATES_DIR = WORKSPACE / "templates"
SCRIPTS_DIR = WORKSPACE / "scripts"

IS_VERCEL = bool(os.environ.get("VERCEL"))

if IS_VERCEL:
    _tmp = Path("/tmp/spendops")
    _tmp.mkdir(exist_ok=True)
    DB_PATH    = _tmp / "spendops.db"
    OUTPUTS_DIR = _tmp / "outputs"
    DATA_DIR   = _tmp / "data"
    UPLOADS_DIR = _tmp / "uploads"
else:
    DB_PATH    = WORKSPACE / "spendops.db"
    OUTPUTS_DIR = WORKSPACE / "outputs"
    DATA_DIR   = WORKSPACE / "data"
    UPLOADS_DIR = WORKSPACE / "uploads"

OUTPUTS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)

# On Vercel: seed the DB from the bundled spendops_seed.db on first cold start
if IS_VERCEL and not DB_PATH.exists():
    seed = WORKSPACE / "spendops_seed.db"
    if seed.exists():
        shutil.copy2(str(seed), str(DB_PATH))
    else:
        # Fallback: initialise an empty schema
        sys.path.insert(0, str(SCRIPTS_DIR))
        from init_db import init as _init_db
        _init_db(str(DB_PATH))

# ---------------------------------------------------------------------------
# Auth (optional — only active when SPENDOPS_AUTH_PASSWORD is set)
# ---------------------------------------------------------------------------
security = HTTPBasic(auto_error=False)
AUTH_PASSWORD = os.environ.get("SPENDOPS_AUTH_PASSWORD", "")


def check_auth(request: Request, credentials: Optional[HTTPBasicCredentials] = Depends(security)):
    if not AUTH_PASSWORD:
        return  # auth disabled — SPENDOPS_AUTH_PASSWORD not set
    # Skip auth for localhost regardless of env var (never prompt on local dev)
    host = request.headers.get("host", "").split(":")[0]
    if host in ("localhost", "127.0.0.1", "::1"):
        return
    if credentials is None:
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Basic"})
    ok_user = secrets.compare_digest(credentials.username.encode(), b"spendops")
    ok_pass = secrets.compare_digest(credentials.password.encode(), AUTH_PASSWORD.encode())
    if not (ok_user and ok_pass):
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Basic"})


# ---------------------------------------------------------------------------
# Pipeline state (simple in-memory; fine for single-user local/Vercel)
# ---------------------------------------------------------------------------
_pipeline_state = {"running": False, "current_step": "", "pct_complete": 0, "log": []}


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------
def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


CONTRACT_FIELDS = {"product_name", "vendor_id", "owner_name", "renewal_date",
                   "annual_cost", "auto_renew", "notes"}


def resolve_vendor_id(conn, vendor_name: str) -> int | None:
    """Return vendor.id for a given name, creating the vendor row if it doesn't exist."""
    if not vendor_name or not vendor_name.strip():
        return None
    name = vendor_name.strip()
    row = conn.execute(
        "SELECT id FROM vendors WHERE LOWER(name)=LOWER(?)", (name,)
    ).fetchone()
    if row:
        return row[0]
    cur = conn.execute("INSERT INTO vendors (name) VALUES (?)", (name,))
    return cur.lastrowid


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="SpendOps", version="2.0")


# ---------------------------------------------------------------------------
# Dashboard HTML
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse, dependencies=[Depends(check_auth)])
async def serve_dashboard():
    html_path = TEMPLATES_DIR / "dashboard.html"
    if not html_path.exists():
        # Fall back to outputs/ during migration
        html_path = OUTPUTS_DIR / "dashboard.html"
    if not html_path.exists():
        return HTMLResponse("<h1>Dashboard not found. Run the pipeline first.</h1>", status_code=404)
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Results: merged agent outputs
# ---------------------------------------------------------------------------
@app.get("/api/results", dependencies=[Depends(check_auth)])
async def get_results():
    result = {}
    for name in ["forecast_summary", "renewal_risk", "run_rate_forecast",
                 "anomaly_detect", "consolidation_suggest", "orchestrator", "narrative_brief"]:
        p = OUTPUTS_DIR / f"{name}.json"
        if p.exists():
            result[name] = json.loads(p.read_text(encoding="utf-8"))
    return result


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Budget lines (non-subscription) — Personnel, Hardware, Support, etc.
# ---------------------------------------------------------------------------
@app.get("/api/budget-lines", dependencies=[Depends(check_auth)])
async def get_budget_lines():
    conn = get_conn()
    rows = conn.execute("""
        SELECT bl.id, c.name AS category, bl.description,
               ROUND(SUM(bm.planned_amount), 0)  AS plan_annual,
               ROUND(SUM(COALESCE(bm.actual_amount, 0)), 0) AS actual_ytd
        FROM budget_lines bl
        JOIN categories c ON bl.category_id = c.id
        JOIN budget_months bm ON bm.budget_line_id = bl.id
        WHERE bl.department_id = (SELECT id FROM departments WHERE name='IT/OT')
          AND bl.cycle_id      = (SELECT id FROM budget_cycles  WHERE name='FY2026')
          AND bl.subscription_id IS NULL
        GROUP BY bl.id
        ORDER BY c.name, bl.description
    """).fetchall()
    conn.close()
    result = []
    for r in rows:
        plan = r[3] or 0
        ytd  = r[4] or 0
        result.append({
            "id":          r[0],
            "category":    r[1],
            "description": r[2],
            "plan_annual": plan,
            "actual_ytd":  ytd,
            "pct_consumed": round(ytd / plan * 100, 1) if plan > 0 else 0,
        })
    return result


@app.put("/api/budget-lines/{line_id}", dependencies=[Depends(check_auth)])
async def update_budget_line(line_id: int, body: dict):
    conn = get_conn()
    # Verify line exists and belongs to IT/OT FY2026
    row = conn.execute(
        "SELECT id FROM budget_lines WHERE id=? AND subscription_id IS NULL", (line_id,)
    ).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Budget line not found")

    if "description" in body:
        conn.execute("UPDATE budget_lines SET description=? WHERE id=?",
                     (str(body["description"]), line_id))

    if "plan_annual" in body:
        new_annual = float(body["plan_annual"] or 0)
        months = conn.execute(
            "SELECT id FROM budget_months WHERE budget_line_id=?", (line_id,)
        ).fetchall()
        if months:
            monthly = round(new_annual / len(months), 2)
            conn.execute(
                "UPDATE budget_months SET planned_amount=? WHERE budget_line_id=?",
                (monthly, line_id)
            )

    conn.commit()
    conn.close()
    return {"ok": True}


@app.post("/api/budget-lines", dependencies=[Depends(check_auth)])
async def create_budget_line(body: dict):
    description = str(body.get("description", "New budget line")).strip()
    category    = str(body.get("category", "Personnel"))
    plan_annual = float(body.get("plan_annual", 0) or 0)

    conn = get_conn()
    dept_id  = conn.execute("SELECT id FROM departments WHERE name='IT/OT'").fetchone()[0]
    cycle    = conn.execute(
        "SELECT id, start_date, end_date FROM budget_cycles WHERE name='FY2026'"
    ).fetchone()
    cycle_id, start_date, end_date = cycle

    cat_row = conn.execute("SELECT id FROM categories WHERE name=?", (category,)).fetchone()
    if not cat_row:
        conn.close()
        raise HTTPException(status_code=400, detail=f"Category '{category}' not found")
    cat_id = cat_row[0]

    conn.execute(
        "INSERT INTO budget_lines (department_id, cycle_id, category_id, description) VALUES (?,?,?,?)",
        (dept_id, cycle_id, cat_id, description)
    )
    line_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    # Generate 12 monthly budget_months rows
    from datetime import date
    monthly = round(plan_annual / 12, 2) if plan_annual else 0
    start   = date.fromisoformat(start_date)
    for m in range(12):
        mo = ((start.month - 1 + m) % 12) + 1
        yr = start.year + ((start.month - 1 + m) // 12)
        month_str = f"{yr}-{mo:02d}"
        conn.execute(
            "INSERT INTO budget_months (budget_line_id, month, planned_amount) VALUES (?,?,?)",
            (line_id, month_str, monthly)
        )

    conn.commit()
    conn.close()
    return {"ok": True, "id": line_id}


@app.delete("/api/budget-lines/{line_id}", dependencies=[Depends(check_auth)])
async def delete_budget_line(line_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM budget_months WHERE budget_line_id=?", (line_id,))
    conn.execute("DELETE FROM budget_lines WHERE id=? AND subscription_id IS NULL", (line_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Budget settings — read and update the approved budget
# ---------------------------------------------------------------------------
@app.get("/api/budget-settings", dependencies=[Depends(check_auth)])
async def get_budget_settings():
    conn = get_conn()
    approved = conn.execute(
        "SELECT COALESCE(SUM(planned_amount),0) FROM budget_months"
    ).fetchone()[0]
    dept = conn.execute("SELECT name FROM departments WHERE id=1").fetchone()
    cycle = conn.execute(
        "SELECT name, start_date, end_date FROM budget_cycles WHERE id=1"
    ).fetchone()
    conn.close()
    return {
        "approved_budget": round(approved, 2),
        "department": dept[0] if dept else "IT/OT",
        "cycle": cycle[0] if cycle else "FY2026",
        "cycle_start": cycle[1] if cycle else "",
        "cycle_end": cycle[2] if cycle else "",
    }


@app.put("/api/budget-settings", dependencies=[Depends(check_auth)])
async def update_budget_settings(body: dict):
    new_total = float(body.get("approved_budget", 0))
    if new_total <= 0:
        raise HTTPException(status_code=400, detail="approved_budget must be > 0")
    conn = get_conn()
    current = conn.execute(
        "SELECT COALESCE(SUM(planned_amount),0) FROM budget_months"
    ).fetchone()[0]
    if current > 0:
        # Scale all planned_amount values proportionally to hit the new total
        scale = new_total / current
        conn.execute("UPDATE budget_months SET planned_amount = ROUND(planned_amount * ?, 2)", (scale,))
    conn.commit()
    conn.close()
    return {"ok": True, "approved_budget": new_total}


# DB status — quick health check
# ---------------------------------------------------------------------------
@app.get("/api/db-status", dependencies=[Depends(check_auth)])
async def db_status():
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM subscriptions").fetchone()[0]
    total = conn.execute("SELECT COALESCE(SUM(annual_cost),0) FROM subscriptions").fetchone()[0]
    missing_owners = conn.execute(
        "SELECT COUNT(*) FROM subscriptions WHERE owner_name IS NULL OR owner_name='' OR owner_name='VACANT'"
    ).fetchone()[0]
    conn.close()
    return {
        "db_path": str(DB_PATH),
        "contract_count": count,
        "total_annual_cost": round(total, 2),
        "missing_owners": missing_owners,
        "persists_on_restart": True,
    }


# ---------------------------------------------------------------------------
# Vendors list
# ---------------------------------------------------------------------------
@app.get("/api/vendors", dependencies=[Depends(check_auth)])
async def list_vendors():
    conn = get_conn()
    rows = conn.execute("SELECT id, name FROM vendors ORDER BY name ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Contract CRUD
# ---------------------------------------------------------------------------
@app.get("/api/contracts", dependencies=[Depends(check_auth)])
async def list_contracts():
    conn = get_conn()
    rows = conn.execute("""
        SELECT s.id, v.name as vendor, s.product_name, s.owner_name,
               s.renewal_date, s.annual_cost, s.auto_renew, s.notes,
               s.department_id, s.vendor_id
        FROM subscriptions s
        LEFT JOIN vendors v ON v.id = s.vendor_id
        ORDER BY s.renewal_date ASC NULLS LAST
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/contracts", dependencies=[Depends(check_auth)])
async def create_contract(body: dict):
    fields = {k: v for k, v in body.items() if k in CONTRACT_FIELDS}
    conn = get_conn()
    # Resolve vendor_name → vendor_id
    if "vendor_name" in body and body["vendor_name"]:
        vid = resolve_vendor_id(conn, body["vendor_name"])
        if vid:
            fields["vendor_id"] = vid
    fields.setdefault("department_id", 1)
    fields.setdefault("product_name", "New Contract")
    fields.setdefault("annual_cost", 0)
    fields.setdefault("auto_renew", 0)

    cols = ", ".join(fields.keys())
    placeholders = ", ".join("?" * len(fields))
    cur = conn.execute(
        f"INSERT INTO subscriptions ({cols}) VALUES ({placeholders})",
        list(fields.values())
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return {"ok": True, "id": new_id}


@app.put("/api/contracts/{contract_id}", dependencies=[Depends(check_auth)])
async def update_contract(contract_id: int, body: dict):
    conn = get_conn()
    updates = {k: v for k, v in body.items() if k in CONTRACT_FIELDS}
    # Resolve vendor_name → vendor_id if caller sent the display name
    if "vendor_name" in body:
        vid = resolve_vendor_id(conn, body["vendor_name"])
        if vid:
            updates["vendor_id"] = vid
        updates.pop("vendor_name", None)
    if not updates:
        conn.close()
        raise HTTPException(status_code=400, detail="No valid fields to update")
    set_clause = ", ".join(f"{k}=?" for k in updates)
    conn.execute(
        f"UPDATE subscriptions SET {set_clause} WHERE id=?",
        list(updates.values()) + [contract_id]
    )
    conn.commit()
    conn.close()
    return {"ok": True, "id": contract_id}


@app.delete("/api/contracts/{contract_id}", dependencies=[Depends(check_auth)])
async def delete_contract(contract_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM subscriptions WHERE id=?", (contract_id,))
    conn.commit()
    conn.close()
    return {"ok": True, "id": contract_id}


# ---------------------------------------------------------------------------
# Pipeline: trigger + SSE progress + polling status
# ---------------------------------------------------------------------------
PIPELINE_STEPS = [
    ("read_db",              "Exporting database"),
    ("calc_forecast",        "Computing forecasts"),
    ("renewal_risk",         "Analyzing renewal risk"),
    ("run_rate_forecast",    "Run-rate forecast"),
    ("anomaly_detect",       "Detecting anomalies"),
    ("consolidation_suggest","Finding consolidation opportunities"),
    ("orchestrator",         "Orchestrating outputs"),
    ("narrative_brief",      "Generating narrative"),
]


def _run_pipeline_sync(department: str, cycle: str, today: str, ai_backend: str):
    """Run the full pipeline synchronously, updating _pipeline_state as steps complete."""
    global _pipeline_state
    py = sys.executable
    scripts = str(SCRIPTS_DIR)
    db = str(DB_PATH)
    out = str(OUTPUTS_DIR)
    data = str(DATA_DIR)

    total = len(PIPELINE_STEPS)
    _pipeline_state.update({"running": True, "current_step": "", "pct_complete": 0, "log": []})

    def run_step(label, cmd):
        _pipeline_state["current_step"] = label
        _pipeline_state["log"].append(f"Starting: {label}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            _pipeline_state["log"].append(f"WARNING: {label} exited {result.returncode}")
        else:
            _pipeline_state["log"].append(f"Done: {label}")

    # Step 0: read_db
    step_idx = 0
    _pipeline_state["pct_complete"] = int(step_idx / total * 100)
    run_step("Exporting database", [
        py, f"{scripts}/read_db.py",
        "--department", department, "--cycle", cycle,
        "--db", db, "--output-dir", data
    ])
    step_idx += 1

    # Step 1: calc_forecast
    _pipeline_state["pct_complete"] = int(step_idx / total * 100)
    run_step("Computing forecasts", [
        py, f"{scripts}/calc_forecast.py",
        "--department", department, "--cycle", cycle,
        "--today", today, "--db", db,
        "--output", f"{out}/forecast_summary.json"
    ])
    step_idx += 1

    # Steps 2-7: agents (skip html_dashboard_builder — reactive template handles display)
    agents = ["renewal_risk", "run_rate_forecast", "anomaly_detect",
              "consolidation_suggest", "orchestrator", "narrative_brief"]
    for agent in agents:
        _pipeline_state["pct_complete"] = int(step_idx / total * 100)
        label = next((l for s, l in PIPELINE_STEPS if s == agent), agent)
        run_step(label, [
            py, f"{scripts}/run_agent.py",
            "--agent", agent,
            "--department", department,
            "--today", today,
            "--data-dir", data,
            "--forecast-summary", f"{out}/forecast_summary.json",
            "--prior-outputs-dir", out,
            "--output", f"{out}/{agent}.json",
            "--ai-backend", ai_backend,
        ])
        step_idx += 1

    # NOTE: templates/dashboard.html is the reactive template — never overwrite it.
    # All computed data is served via /api/results; the template reads it dynamically.

    _pipeline_state.update({"running": False, "current_step": "complete", "pct_complete": 100})


@app.post("/api/run-analysis", dependencies=[Depends(check_auth)])
async def run_analysis(body: dict = {}):
    if _pipeline_state["running"]:
        return {"ok": False, "message": "Pipeline already running"}
    department = body.get("department", "IT/OT")
    cycle = body.get("cycle", "FY2026")
    today = body.get("today", date.today().strftime("%Y-%m-%d"))
    ai_backend = body.get("ai_backend", "openrouter")

    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, _run_pipeline_sync, department, cycle, today, ai_backend)
    return {"ok": True, "message": "Pipeline started"}


@app.get("/api/analysis-stream", dependencies=[Depends(check_auth)])
async def analysis_stream():
    """Server-Sent Events stream. Polls pipeline state every second."""
    async def event_generator():
        last_log_len = 0
        while True:
            state = _pipeline_state.copy()
            data = {
                "running": state["running"],
                "current_step": state["current_step"],
                "pct_complete": state["pct_complete"],
            }
            # Send new log lines
            new_logs = state["log"][last_log_len:]
            for log_line in new_logs:
                data["log"] = log_line
                last_log_len += 1
            yield f"data: {json.dumps(data)}\n\n"
            if not state["running"] and state["current_step"] == "complete":
                break
            await asyncio.sleep(1)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/analysis-status", dependencies=[Depends(check_auth)])
async def analysis_status():
    """Polling fallback for SSE-unfriendly environments."""
    return {
        "running": _pipeline_state["running"],
        "current_step": _pipeline_state["current_step"],
        "pct_complete": _pipeline_state["pct_complete"],
    }


# ---------------------------------------------------------------------------
# SpendOps Analyst chat
# ---------------------------------------------------------------------------
@app.post("/api/analyst", dependencies=[Depends(check_auth)])
async def analyst_chat(body: dict):
    question = body.get("question", "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="No question provided")

    # Build context from latest outputs
    context = {}
    for name in ["forecast_summary", "orchestrator", "narrative_brief", "renewal_risk", "anomaly_detect"]:
        p = OUTPUTS_DIR / f"{name}.json"
        if p.exists():
            context[name] = json.loads(p.read_text())

    system = (
        "You are SpendOps Analyst — a spend intelligence expert for IT/OT department budgets. "
        "Answer concisely and precisely, citing specific vendors, amounts, and dates from the data. "
        "If the data does not contain enough information to answer, say so. "
        "Never invent numbers."
    )
    user_msg = f"Current spend data:\n{json.dumps(context, indent=2)}\n\nQuestion: {question}"

    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not openrouter_key:
        return {"answer": "OPENROUTER_API_KEY not configured. Add it to your .env file.", "model": "none"}

    try:
        from openai import OpenAI
        client = OpenAI(api_key=openrouter_key, base_url="https://openrouter.ai/api/v1")
        response = client.chat.completions.create(
            model="openrouter/auto",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=1024,
            temperature=0.2,
            extra_headers={"X-Title": "SpendOps Analyst"},
        )
        answer = response.choices[0].message.content
        model_used = getattr(response, "model", "auto")
        return {"answer": answer, "model": model_used}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Data upload + schema inference
# ---------------------------------------------------------------------------
@app.post("/api/upload-data", dependencies=[Depends(check_auth)])
async def upload_data(file: UploadFile = File(...)):
    contents = await file.read()
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".csv", ".xlsx", ".xls"}:
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")

    save_path = UPLOADS_DIR / file.filename
    save_path.write_bytes(contents)

    try:
        # Import infer_schema lazily
        sys.path.insert(0, str(SCRIPTS_DIR))
        from infer_schema import infer_schema
        schema = infer_schema(str(save_path))
    except Exception as e:
        return {"file": file.filename, "error": str(e), "inferred_schema": None, "import_ready": False}

    return {
        "file": file.filename,
        "inferred_schema": schema,
        "import_ready": schema.get("confidence", 0) > 0.7,
    }


# ---------------------------------------------------------------------------
# Dev entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
