---
name: spendops-run-calc
description: >
  Runs the SpendOps forecast pre-computation script.
  Use before any forecast or budget analysis.
  Produces forecast_summary.json in the outputs folder.
metadata:
  openclaw:
    emoji: "🔢"
    requires:
      bins: ["py"]
allowed-tools: ["exec"]
---

# SpendOps Run-Calc Skill

Pre-computes rolling average forecasts before any LLM analysis. Always run this before spendops-orchestrator.

## How to run

```
py C:\Users\puebl\.openclaw\workspace-spendops\scripts\calc_forecast.py --department "IT/OT" --cycle "FY2026" --db "C:\Users\puebl\.openclaw\workspace-spendops\spendops.db" --output "C:\Users\puebl\.openclaw\workspace-spendops\outputs\forecast_summary.json"
```

## After running

Read the output and report the key numbers:
- Budget total
- Actual YTD
- Forecast EOY
- Variance vs plan
