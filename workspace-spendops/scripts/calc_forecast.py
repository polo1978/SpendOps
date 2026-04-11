#!/usr/bin/env python3
"""
SpendOps - Forecast pre-computation script
Computes rolling average forecasts BEFORE calling any LLM.
The LLM receives the results and explains them. It does NOT recalculate.

Usage: python3 scripts/calc_forecast.py --department IT --cycle FY2026 --today 2026-03-05 --db ./spendops.db --output ./outputs/forecast_summary.json
"""

import sqlite3
import json
import argparse
import os
from datetime import datetime, date
from collections import defaultdict

def get_months_in_cycle(start_date_str, end_date_str):
    """Returns list of YYYY-MM strings for the cycle."""
    start = datetime.strptime(start_date_str, "%Y-%m-%d")
    end = datetime.strptime(end_date_str, "%Y-%m-%d")
    months = []
    current = date(start.year, start.month, 1)
    while current <= end.date():
        months.append(current.strftime("%Y-%m"))
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)
    return months

def rolling_average(values, window=3):
    """Last N non-zero values average."""
    non_zero = [v for v in values if v and v > 0]
    if not non_zero:
        return 0.0
    return sum(non_zero[-window:]) / len(non_zero[-window:])

def run(db_path, department, cycle, today_str, output_path):
    conn = sqlite3.connect(db_path)
    today = datetime.strptime(today_str, "%Y-%m-%d").date()

    # Fetch IDs
    dept = conn.execute("SELECT id FROM departments WHERE name=?", (department,)).fetchone()
    if not dept:
        print(f"ERROR: Department '{department}' not found.")
        conn.close()
        return False
    dept_id = dept[0]

    cyc = conn.execute("SELECT id, start_date, end_date FROM budget_cycles WHERE name=?", (cycle,)).fetchone()
    if not cyc:
        print(f"ERROR: Cycle '{cycle}' not found.")
        conn.close()
        return False
    cycle_id, start_date, end_date = cyc

    all_months = get_months_in_cycle(start_date, end_date)

    # Fetch budget lines
    lines = conn.execute(
        "SELECT id, category_id, subscription_id FROM budget_lines WHERE department_id=? AND cycle_id=?",
        (dept_id, cycle_id)
    ).fetchall()

    # Fetch categories for breakdown
    cats = {r[0]: r[1] for r in conn.execute("SELECT id, name FROM categories").fetchall()}

    # Fetch subscription renewal costs
    sub_renewal = {}
    for row in conn.execute("SELECT id, renewal_date, annual_cost FROM subscriptions WHERE department_id=?", (dept_id,)):
        sub_id, rdate, cost = row
        if rdate and cost:
            sub_renewal[sub_id] = {"renewal_date": rdate, "monthly_cost": cost / 12}

    total_plan = 0.0
    total_actual_ytd = 0.0
    total_forecast_eoy = 0.0
    category_totals = defaultdict(lambda: {"actual_ytd": 0.0, "forecast_eoy": 0.0})

    for line_id, cat_id, sub_id in lines:
        months_data = conn.execute(
            "SELECT month, planned_amount, actual_amount FROM budget_months WHERE budget_line_id=? ORDER BY month",
            (line_id,)
        ).fetchall()

        month_map = {m: {"planned": p, "actual": a} for m, p, a in months_data}

        # Compute plan total
        line_plan = sum(v["planned"] for v in month_map.values())
        total_plan += line_plan

        # Actuals up to today
        actuals_ordered = []
        actual_ytd = 0.0
        for m in all_months:
            m_date = datetime.strptime(m + "-01", "%Y-%m-%d").date()
            if m_date <= today:
                a = month_map.get(m, {}).get("actual", 0.0) or 0.0
                actuals_ordered.append(a)
                actual_ytd += a

        total_actual_ytd += actual_ytd

        # Rolling average for remaining months
        avg = rolling_average(actuals_ordered)
        line_forecast = actual_ytd

        for m in all_months:
            m_date = datetime.strptime(m + "-01", "%Y-%m-%d").date()
            if m_date > today:
                # Check subscription renewal overlay
                step = 0.0
                if sub_id and sub_id in sub_renewal:
                    rdate = sub_renewal[sub_id]["renewal_date"]
                    r_month = rdate[:7]  # YYYY-MM
                    if r_month == m:
                        step = sub_renewal[sub_id]["monthly_cost"]

                month_forecast = max(avg, step) if step > 0 else avg
                line_forecast += month_forecast

                # Write back to DB
                conn.execute(
                    """UPDATE budget_months SET precomputed_forecast = ?
                       WHERE budget_line_id = ? AND month = ?""",
                    (month_forecast, line_id, m)
                )

        total_forecast_eoy += line_forecast
        cat_name = cats.get(cat_id, "Unknown")
        category_totals[cat_name]["actual_ytd"] += actual_ytd
        category_totals[cat_name]["forecast_eoy"] += line_forecast

    conn.commit()
    conn.close()

    # Plan-based forecast: scale plan by actual/plan ratio so far
    months_elapsed = sum(1 for m in all_months if datetime.strptime(m + "-01", "%Y-%m-%d").date() <= today)
    months_total = len(all_months)
    plan_fraction = (months_elapsed / months_total) if months_total else 0
    if plan_fraction > 0 and total_plan > 0:
        run_rate_vs_plan = total_actual_ytd / (total_plan * plan_fraction)
        forecast_eoy_plan = total_plan * run_rate_vs_plan
    else:
        forecast_eoy_plan = total_plan

    # Blended: average of rolling and plan-based
    forecast_eoy_blended = (total_forecast_eoy + forecast_eoy_plan) / 2

    summary = {
        "department": department,
        "cycle": cycle,
        "today": today_str,
        "budget_total": round(total_plan, 2),
        "actual_ytd": round(total_actual_ytd, 2),
        "forecast_eoy_rolling": round(total_forecast_eoy, 2),
        "forecast_eoy_plan": round(forecast_eoy_plan, 2),
        "forecast_eoy_blended": round(forecast_eoy_blended, 2),
        "variance_vs_budget": round(forecast_eoy_blended - total_plan, 2),
        "category_breakdown": [
            {
                "category": cat,
                "actual_ytd": round(vals["actual_ytd"], 2),
                "forecast_eoy": round(vals["forecast_eoy"], 2)
            }
            for cat, vals in sorted(category_totals.items())
        ]
    }

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"Forecast summary written to: {output_path}")
    print(f"  Budget total:      ${summary['budget_total']:,.2f}")
    print(f"  Actual YTD:        ${summary['actual_ytd']:,.2f}")
    print(f"  Forecast EOY:      ${summary['forecast_eoy_blended']:,.2f}")
    print(f"  Variance vs plan:  ${summary['variance_vs_budget']:,.2f}")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SpendOps forecast pre-computation")
    parser.add_argument("--department", required=True)
    parser.add_argument("--cycle", required=True)
    parser.add_argument("--today", default=date.today().strftime("%Y-%m-%d"))
    parser.add_argument("--db", default="./spendops.db")
    parser.add_argument("--output", default="./outputs/forecast_summary.json")
    args = parser.parse_args()
    ok = run(args.db, args.department, args.cycle, args.today, args.output)
    exit(0 if ok else 1)
