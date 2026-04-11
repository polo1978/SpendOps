---
name: spendops-orchestrator
description: >
  Full SpendOps multi-agent pipeline. Use when the user asks for a spend brief,
  budget analysis, renewal report, anomaly check, consolidation suggestions,
  or a dashboard for a department. Calls LM Studio locally via the AI adapter.
  Requires spendops-run-calc to have been called first (forecast_summary.json must exist).
  Produces a brief JSON and a self-contained HTML dashboard file in the outputs/ folder.
metadata:
  openclaw:
    emoji: "📊"
    requires:
      bins: ["python3", "curl"]
allowed-tools: ["bash", "exec", "read_file", "write_file"]
---

# SpendOps Orchestrator Skill

This skill runs the full SpendOps agent pipeline against the local LM Studio model.

## Prerequisites

- LM Studio must be running with a Qwen model loaded.
- Server must be reachable at http://127.0.0.1:1234/v1
- `spendops-run-calc` must have been called first — `forecast_summary.json` must exist in the workspace.
- `spendops-read-db` must have been called — data JSON files must exist in workspace/data/.

## What this skill does

Calls each specialist agent in sequence via LM Studio, validates JSON output, merges into a brief, and builds an HTML dashboard.

Pipeline order:
1. RenewalRisk
2. RunRateForecast (uses forecast_summary.json — no arithmetic by the LLM)
3. AnomalyDetect
4. ConsolidationSuggest
5. Orchestrator merge
6. NarrativeBrief
7. HTMLDashboardBuilder

## How to call each agent via LM Studio

Use the run_agent.py script located at scripts/run_agent.py.

```bash
python3 scripts/run_agent.py \
  --agent renewal_risk \
  --department "IT" \
  --today "$(date +%Y-%m-%d)" \
  --data-dir ./data/ \
  --output ./outputs/renewal_risk.json
```

Repeat for each agent, substituting the agent name. Valid agent names:
- renewal_risk
- run_rate_forecast
- anomaly_detect
- consolidation_suggest
- orchestrator
- narrative_brief
- html_dashboard_builder

## Validation

After each agent call, run_agent.py checks that the output is valid JSON with the required top-level keys. If validation fails, it retries once with this suffix appended to the user prompt:
"Return only raw JSON with no markdown formatting, no code fences, no explanation."

If it fails twice, it writes an error object: `{"error": "reason", "agent": "agent_name"}` and continues.

## Output files

- outputs/renewal_risk.json
- outputs/run_rate_forecast.json
- outputs/anomaly_detect.json
- outputs/consolidation_suggest.json
- outputs/brief_DEPARTMENT_DATE.json
- outputs/narrative_DEPARTMENT_DATE.json
- outputs/dashboard_DEPARTMENT_DATE.html  ← open this in your browser

## Full pipeline run (one command)

```bash
python3 scripts/run_pipeline.py \
  --department "IT" \
  --cycle "FY2026" \
  --db ./spendops.db \
  --output-dir ./outputs/
```

This runs all steps in order. Check ./outputs/ for results.

## Checking LM Studio is up

```bash
curl -s http://127.0.0.1:1234/v1/models | python3 -m json.tool
```

If this returns model info, LM Studio is ready. If it fails, start the local server inside LM Studio first.
