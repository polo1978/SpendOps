#!/usr/bin/env python3
"""
SpendOps - Full pipeline runner
Runs all agents in order: read_db -> calc_forecast -> all specialists -> orchestrator -> narrative -> dashboard.

Usage: py scripts/run_pipeline.py --department "IT/OT" --cycle FY2026 --db ./spendops.db --output-dir ./outputs/
       py scripts/run_pipeline.py --department "IT/OT" --cycle FY2026 --ai-backend lmstudio  # use local LM Studio
"""

import argparse
import subprocess
import sys
import os
from datetime import date

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
except ImportError:
    pass

AGENTS_IN_ORDER = [
    "renewal_risk",
    "run_rate_forecast",
    "anomaly_detect",
    "consolidation_suggest",
    "orchestrator",
    "narrative_brief",
    "html_dashboard_builder",
]

def run(cmd_parts, label):
    print(f"\n{'='*50}")
    print(f"STEP: {label}")
    print(f"{'='*50}")
    result = subprocess.run(cmd_parts)
    if result.returncode != 0:
        print(f"WARNING: {label} exited with code {result.returncode}. Continuing...")
    return result.returncode == 0

def main():
    parser = argparse.ArgumentParser(description="Run full SpendOps pipeline")
    parser.add_argument("--department", required=True)
    parser.add_argument("--cycle", required=True)
    parser.add_argument("--db", default="./spendops.db")
    parser.add_argument("--output-dir", default="./outputs/")
    parser.add_argument("--today", default=date.today().strftime("%Y-%m-%d"))
    parser.add_argument("--ai-backend", choices=["openrouter", "lmstudio"], default="openrouter")
    args = parser.parse_args()

    dept = args.department
    cycle = args.cycle
    today = args.today
    db = os.path.abspath(args.db)
    out = os.path.abspath(args.output_dir)
    ai_backend = args.ai_backend
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_dir = os.path.dirname(scripts_dir)
    data_dir = os.path.join(workspace_dir, "data")

    os.makedirs(out, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    py = sys.executable

    run(
        [py, os.path.join(scripts_dir, "read_db.py"),
         "--department", dept, "--cycle", cycle,
         "--db", db, "--output-dir", data_dir],
        "Export data from database"
    )

    run(
        [py, os.path.join(scripts_dir, "calc_forecast.py"),
         "--department", dept, "--cycle", cycle,
         "--today", today, "--db", db,
         "--output", os.path.join(out, "forecast_summary.json")],
        "Pre-compute forecast (calc_forecast.py)"
    )

    for agent in AGENTS_IN_ORDER:
        output_path = os.path.join(out, f"{agent}.json")
        run(
            [py, os.path.join(scripts_dir, "run_agent.py"),
             "--agent", agent,
             "--department", dept,
             "--today", today,
             "--data-dir", data_dir,
             "--forecast-summary", os.path.join(out, "forecast_summary.json"),
             "--prior-outputs-dir", out,
             "--output", output_path,
             "--ai-backend", ai_backend],
            f"Agent: {agent}"
        )

    dashboard_path = os.path.join(out, "html_dashboard_builder.html")
    brief_path = os.path.join(out, "orchestrator.json")

    print(f"\n{'='*50}")
    print("PIPELINE COMPLETE")
    print(f"{'='*50}")
    print(f"Brief JSON:      {brief_path}")
    print(f"Dashboard HTML:  {dashboard_path}")
    print(f"\nDrag this file into your browser to open the dashboard:")
    print(f"  {dashboard_path}")

if __name__ == "__main__":
    main()