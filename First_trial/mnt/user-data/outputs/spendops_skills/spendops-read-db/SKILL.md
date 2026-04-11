---
name: spendops-read-db
description: >
  Reads SpendOps data from the local SQLite database and exports it as JSON files
  to the workspace data/ folder. Use before any analysis, brief, or dashboard request.
  Filters by department and cycle. Outputs are consumed by the orchestrator skill.
metadata:
  openclaw:
    emoji: "🗄️"
    requires:
      bins: ["python3"]
allowed-tools: ["bash", "exec", "read_file", "write_file"]
---

# SpendOps Read-DB Skill

Exports data from the local SpendOps SQLite database to JSON files.

## How to run

```bash
python3 scripts/read_db.py \
  --department "IT" \
  --cycle "FY2026" \
  --db ./spendops.db \
  --output-dir ./data/
```

## Output files (written to data/ folder)

- data/departments.json
- data/budget_cycles.json
- data/categories.json
- data/budget_lines.json
- data/budget_months.json
- data/vendors.json
- data/subscriptions.json

## Verify it worked

```bash
ls ./data/
python3 -c "import json; d=json.load(open('./data/subscriptions.json')); print(f'{len(d)} subscriptions loaded')"
```

## Notes

- If the database does not exist yet, run: python3 scripts/init_db.py to create it with the correct schema.
- After init_db.py runs, the database is empty. You need to insert your actual data. The easiest way is to have the agent help you import from a CSV or spreadsheet.
- Database path is configured in TOOLS.md. Default: ./spendops.db (relative to workspace).
