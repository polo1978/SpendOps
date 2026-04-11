---
name: spendops-orchestrator
description: >
  Full SpendOps multi-agent pipeline. Use when the user asks for a spend brief,
  budget analysis, renewal report, anomaly check, consolidation suggestions,
  or a dashboard for a department and cycle.
  Runs all agents in sequence via LM Studio and produces an HTML dashboard.
metadata:
  openclaw:
    emoji: "📊"
    requires:
      bins: ["py"]
allowed-tools: ["exec"]
---

# SpendOps Orchestrator Skill

Run the full SpendOps pipeline when the user asks for a spend brief, dashboard, or budget analysis.

## Default values
- Department: IT/OT
- Cycle: FY2026
- DB path: C:\Users\puebl\.openclaw\workspace-spendops\spendops.db
- Output dir: C:\Users\puebl\.openclaw\workspace-spendops\outputs\

## How to run

Use the exec tool to run this command (adjust department and cycle if the user specifies different values):

```
py C:\Users\puebl\.openclaw\workspace-spendops\scripts\run_pipeline.py --department "IT/OT" --cycle "FY2026" --db "C:\Users\puebl\.openclaw\workspace-spendops\spendops.db" --output-dir "C:\Users\puebl\.openclaw\workspace-spendops\outputs"
```

## After the pipeline runs

1. Read the file: C:\Users\puebl\.openclaw\workspace-spendops\outputs\narrative_brief.json
2. Summarize the key findings in plain language to the user.
3. Tell the user the dashboard is ready at: C:\Users\puebl\.openclaw\workspace-spendops\outputs\html_dashboard_builder.html
4. Tell them to open it by running: start C:\Users\puebl\.openclaw\workspace-spendops\outputs\html_dashboard_builder.html

## What to report back

From narrative_brief.json, extract and report:
- Top 3-5 bullet points
- The summary paragraph
- Top actions with priority

If narrative_brief.json is missing or empty, read orchestrator.json instead and summarize the kpis, top_risks, and action_queue fields.