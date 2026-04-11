#!/usr/bin/env python3
"""
SpendOps - Database reader
Exports data to JSON files for agent consumption.
Usage: python3 scripts/read_db.py --department IT --cycle FY2026 --db ./spendops.db --output-dir ./data/
"""

import sqlite3
import json
import argparse
import os

def fetch(conn, sql, params=()):
    cur = conn.execute(sql, params)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]

def export(db_path, department, cycle, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    conn = sqlite3.connect(db_path)

    tables = {
        "departments": "SELECT * FROM departments",
        "budget_cycles": "SELECT * FROM budget_cycles",
        "categories": "SELECT * FROM categories",
        "vendors": "SELECT * FROM vendors",
    }

    dept_row = conn.execute(
        "SELECT id FROM departments WHERE name = ?", (department,)
    ).fetchone()
    if not dept_row:
        print(f"ERROR: Department '{department}' not found in database.")
        conn.close()
        return False
    dept_id = dept_row[0]

    cycle_row = conn.execute(
        "SELECT id FROM budget_cycles WHERE name = ?", (cycle,)
    ).fetchone()
    if not cycle_row:
        print(f"ERROR: Cycle '{cycle}' not found in database.")
        conn.close()
        return False
    cycle_id = cycle_row[0]

    results = {}
    for name, sql in tables.items():
        results[name] = fetch(conn, sql)

    results["subscriptions"] = fetch(
        conn,
        "SELECT * FROM subscriptions WHERE department_id = ?",
        (dept_id,)
    )

    results["budget_lines"] = fetch(
        conn,
        "SELECT * FROM budget_lines WHERE department_id = ? AND cycle_id = ?",
        (dept_id, cycle_id)
    )

    line_ids = [r["id"] for r in results["budget_lines"]]
    if line_ids:
        placeholders = ",".join("?" * len(line_ids))
        results["budget_months"] = fetch(
            conn,
            f"SELECT * FROM budget_months WHERE budget_line_id IN ({placeholders})",
            line_ids
        )
    else:
        results["budget_months"] = []

    conn.close()

    for name, data in results.items():
        path = os.path.join(output_dir, f"{name}.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Exported {len(data)} rows -> {path}")

    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export SpendOps data to JSON")
    parser.add_argument("--department", required=True)
    parser.add_argument("--cycle", required=True)
    parser.add_argument("--db", default="./spendops.db")
    parser.add_argument("--output-dir", default="./data/")
    args = parser.parse_args()
    ok = export(args.db, args.department, args.cycle, args.output_dir)
    exit(0 if ok else 1)
