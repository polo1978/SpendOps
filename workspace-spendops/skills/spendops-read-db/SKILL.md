---
name: spendops-read-db
description: >
  Exports SpendOps data from the local SQLite database to JSON files.
  Use before any analysis or dashboard request.
metadata:
  openclaw:
    emoji: "🗄️"
    requires:
      bins: ["py"]
allowed-tools: ["exec"]
---

# SpendOps Read-DB Skill

Exports data from spendops.db to JSON files in the data folder.

## How to run

```
py C:\Users\puebl\.openclaw\workspace-spendops\scripts\read_db.py --department "IT/OT" --cycle "FY2026" --db "C:\Users\puebl\.openclaw\workspace-spendops\spendops.db" --output-dir "C:\Users\puebl\.openclaw\workspace-spendops\data"
```

## After running

Confirm to the user how many rows were exported for each table.
