---
name: spendops-run-calc
description: >
  Runs the SpendOps forecast pre-computation script (calc_forecast.py).
  Use before any forecast or budget analysis. This computes rolling averages,
  overlays subscription renewal costs, and writes precomputed_forecast into
  budget_months. Must run before spendops-orchestrator. Produces forecast_summary.json.
metadata:
  openclaw:
    emoji: "🔢"
    requires:
      bins: ["python3"]
allowed-tools: ["bash", "exec", "read_file", "write_file"]
---

# SpendOps Run-Calc Skill

Runs the arithmetic pre-computation before any LLM forecast work.

## Why this exists

Local LLMs (including Qwen) are unreliable at multi-step arithmetic. This script does all the math outside the LLM, then injects results so the LLM only explains and formats.

## What the script computes

1. For each budget_line, collects months where actual_amount > 0.
2. Computes a 3-month rolling average of actuals.
3. For remaining months in the cycle, uses rolling average as precomputed_forecast.
4. Overlays subscription renewal costs (annual_cost / 12) as a step change for each renewal month.
5. Writes results back into budget_months.precomputed_forecast in the database.
6. Outputs forecast_summary.json with: forecast_eoy_rolling, forecast_eoy_plan, forecast_eoy_blended, budget_total, actual_ytd, variance_vs_budget.

## How to run

```bash
python3 scripts/calc_forecast.py \
  --department "IT" \
  --cycle "FY2026" \
  --today "$(date +%Y-%m-%d)" \
  --db ./spendops.db \
  --output ./outputs/forecast_summary.json
```

## Output

forecast_summary.json in the outputs/ folder. This file is passed to the RunRateForecast agent. The LLM receives this file and explains the numbers — it does not recalculate them.

## Verify it worked

```bash
cat ./outputs/forecast_summary.json
```

You should see: forecast_eoy_rolling, forecast_eoy_plan, forecast_eoy_blended, budget_total, actual_ytd, variance_vs_budget, and a breakdown by category.
