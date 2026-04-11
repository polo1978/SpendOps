#!/usr/bin/env python3
"""
SpendOps - Full pipeline runner
Runs all agents in order: read_db -> calc_forecast -> all specialists -> orchestrator -> narrative -> dashboard.

Usage: python3 scripts/run_pipeline.py --department IT --cycle FY2026 --db ./spendops.db --output-dir ./outputs/
"""

import argparse
import subprocess
import sys
import os
from datetime import date

AGENTS_IN_ORDER = [
    "renewal_risk",
    "run_rate_forecast",
    "anomaly_detect",
    "consolidation_suggest",
    "orchestrator",
    "narrative_brief",
    "html_dashboard_builder",
]

def run(cmd, label):
    print(f"\n{'='*50}")
    print(f"STEP: {label}")
    print(f"{'='*50}")
    result = subprocess.run(cmd, shell=True)
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
    args = parser.parse_args()

    dept = args.department
    cycle = args.cycle
    today = args.today
    db = args.db
    out = args.output_dir
    scripts_dir = os.path.dirname(os.path.abspath(__file__))

    os.makedirs(out, exist_ok=True)
    os.makedirs("./data/", exist_ok=True)

    # Step 1: Export data from DB
    run(
        f"python3 {scripts_dir}/read_db.py --department '{dept}' --cycle '{cycle}' --db '{db}' --output-dir ./data/",
        "Export data from database"
    )

    # Step 2: Compute forecast (before any LLM call)
    run(
        f"python3 {scripts_dir}/calc_forecast.py --department '{dept}' --cycle '{cycle}' --today '{today}' --db '{db}' --output '{out}/forecast_summary.json'",
        "Pre-compute forecast (calc_forecast.py)"
    )

    # Step 3: Run all agents
    for agent in AGENTS_IN_ORDER:
        if agent == "html_dashboard_builder":
            output_path = f"{out}/html_dashboard_builder.json"
        else:
            output_path = f"{out}/{agent}.json"
        run(
            f"python3 {scripts_dir}/run_agent.py --agent '{agent}' --department '{dept}' --today '{today}' --data-dir ./data/ --forecast-summary '{out}/forecast_summary.json' --prior-outputs-dir '{out}' --output '{output_path}'",
            f"Agent: {agent}"
        )

    # Summary
    dept_slug = dept.lower().replace(" ", "_")
    dashboard_path = f"{out}/html_dashboard_builder.html"
    brief_path = f"{out}/orchestrator.json"

    print(f"\n{'='*50}")
    print("PIPELINE COMPLETE")
    print(f"{'='*50}")
    print(f"Brief JSON:      {brief_path}")
    print(f"Dashboard HTML:  {dashboard_path}")
    print(f"\nOpen the dashboard: open '{dashboard_path}'  (or drag it into your browser)")

if __name__ == "__main__":
    main()
