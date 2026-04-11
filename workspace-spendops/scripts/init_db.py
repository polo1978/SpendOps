#!/usr/bin/env python3
"""
SpendOps - Database initializer
Creates the SQLite schema. Run once on setup.
Usage: python3 scripts/init_db.py --db ./spendops.db
"""

import sqlite3
import argparse

SCHEMA = """
CREATE TABLE IF NOT EXISTS departments (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS budget_cycles (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL UNIQUE,
    start_date TEXT NOT NULL,
    end_date   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS categories (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS vendors (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    name    TEXT NOT NULL,
    website TEXT
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id    INTEGER NOT NULL REFERENCES departments(id),
    vendor_id        INTEGER REFERENCES vendors(id),
    product_name     TEXT NOT NULL,
    owner_name       TEXT,
    renewal_date     TEXT,
    term             TEXT,
    auto_renew       INTEGER DEFAULT 0,
    annual_cost      REAL,
    contract_id      TEXT,
    notes            TEXT,
    last_review_date TEXT
);

CREATE TABLE IF NOT EXISTS budget_lines (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_id      INTEGER NOT NULL REFERENCES budget_cycles(id),
    department_id INTEGER NOT NULL REFERENCES departments(id),
    category_id   INTEGER NOT NULL REFERENCES categories(id),
    vendor_id     INTEGER REFERENCES vendors(id),
    subscription_id INTEGER REFERENCES subscriptions(id),
    description   TEXT,
    capex_opex    TEXT DEFAULT 'opex',
    is_recurring  INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS budget_months (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    budget_line_id   INTEGER NOT NULL REFERENCES budget_lines(id),
    month            TEXT NOT NULL,
    planned_amount   REAL DEFAULT 0,
    forecast_amount  REAL DEFAULT 0,
    actual_amount    REAL DEFAULT 0,
    precomputed_forecast REAL
);

CREATE TABLE IF NOT EXISTS insights_briefs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    department_id INTEGER NOT NULL REFERENCES departments(id),
    cycle_id      INTEGER NOT NULL REFERENCES budget_cycles(id),
    created_at    TEXT NOT NULL,
    brief_json    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS insights_items (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    type             TEXT NOT NULL,
    severity         TEXT,
    created_at       TEXT NOT NULL,
    subscription_id  INTEGER REFERENCES subscriptions(id),
    budget_line_id   INTEGER REFERENCES budget_lines(id),
    budget_month_id  INTEGER REFERENCES budget_months(id),
    payload_json     TEXT NOT NULL
);
"""

SEED_CATEGORIES = [
    "Hardware",
    "Software & Licenses",
    "Personnel",
    "Cloud & Infrastructure",
    "Security & Compliance",
    "Support & Outsourcing",
]

def init(db_path):
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    for cat in SEED_CATEGORIES:
        conn.execute(
            "INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,)
        )
    conn.commit()
    conn.close()
    print(f"Database initialized: {db_path}")
    print(f"Categories seeded: {', '.join(SEED_CATEGORIES)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize SpendOps database")
    parser.add_argument("--db", default="./spendops.db", help="Path to SQLite database")
    args = parser.parse_args()
    init(args.db)
