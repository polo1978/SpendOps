#!/usr/bin/env python3
"""
SpendOps - Agent runner
Calls LM Studio with the correct system + user prompt for each specialist agent.
Validates JSON output. Retries once on failure.

Usage: python3 scripts/run_agent.py --agent renewal_risk --department IT --today 2026-03-05 --data-dir ./data/ --forecast-summary ./outputs/forecast_summary.json --output ./outputs/renewal_risk.json
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import date

LM_STUDIO_URL = "http://127.0.0.1:1234/v1/chat/completions"
MODEL = "qwen2.5"  # LM Studio uses the loaded model name; this is passed but LM Studio may ignore it
TEMPERATURE = 0.1
MAX_TOKENS = 4096

AGENT_SCHEMAS = {
    "renewal_risk": ["renewals_next_30_days", "renewals_next_60_days", "renewals_next_90_days", "risks_ranked", "missing_data", "suggested_actions"],
    "run_rate_forecast": ["department", "cycle", "budget_total", "actual_ytd", "forecast_eoy_rolling", "forecast_eoy_blended", "variance_vs_budget"],
    "anomaly_detect": ["anomalies"],
    "consolidation_suggest": ["candidates"],
    "orchestrator": ["department", "cycle", "kpis", "renewals", "top_risks", "action_queue"],
    "narrative_brief": ["bullets", "paragraph", "top_actions"],
    "html_dashboard_builder": None,  # HTML output, no JSON validation
}

SYSTEM_PROMPTS = {
    "renewal_risk": """You are the Renewal Risk Agent for SpendOps. Analyze subscription records and identify renewal-related risks and required actions within the next 90 days.
Do not invent contract terms or costs. If a field is missing, flag it.
Rank risks by urgency and potential financial impact. Include evidence fields and ids.
Return JSON only. No prose before or after the JSON block.""",

    "run_rate_forecast": """You are the Run-Rate Forecast Agent for SpendOps. You receive pre-computed forecast figures and must format them into a structured JSON report with explanations.
Do not recalculate or change any numbers. Do not invent amounts.
Your job is to identify top spending drivers, label assumptions, and assign a confidence level.
If precomputed_forecast values are missing for any month, flag those months in assumptions[].
Return JSON only. No prose before or after the JSON block.""",

    "anomaly_detect": """You are the SpendOps Anomaly Detection Agent. Detect anomalies in planned vs actual vs forecast monthly data and subscription records.
Do not guess causes without evidence. Propose follow-up questions instead of conclusions.
Rank anomalies by severity and dollar impact. Include evidence ids and deltas.
Return JSON only. No prose before or after the JSON block.""",

    "consolidation_suggest": """You are the SpendOps Consolidation Suggestion Agent. Identify possible overlap, redundant subscriptions, and consolidation opportunities.
You must not recommend cancellation without noting operational risk and missing validation data.
Use only provided product names, categories, and descriptions. If cost is unknown, flag it.
Return JSON only. No prose before or after the JSON block.""",

    "orchestrator": """You are the SpendOps Orchestrator. Merge specialist agent outputs into one spend brief and prioritized action queue for a department leader.
Do not invent data. Rank items by urgency and financial impact.
Prioritize: renewals within 90 days, missing ownership, forecast over-budget risk, anomalies, consolidation candidates.
Never modify budget numbers. Include evidence ids for every item.
If any specialist returned an error, include it in the notes array and continue.
Return JSON only. No prose before or after the JSON block.""",

    "narrative_brief": """You are the SpendOps Narrative Agent. Convert structured brief data into a concise leadership-ready summary.
Do not add new facts not present in the input. Keep it to 5 bullets max and 1 short paragraph. Include top 3 actions.
Return JSON only. No prose before or after the JSON block.""",

    "html_dashboard_builder": """You are the SpendOps HTML Dashboard Builder. Produce a single self-contained HTML file.
Requirements: all CSS and JS inline, no external CDN. Dark sidebar navigation. KPI cards, tables, SVG bar chart.
Populate data from the brief JSON. Mark all figures as read-only. Include a Last updated timestamp.
Return the complete HTML file starting with <!DOCTYPE html>. No JSON wrapper. No explanation.""",
}

def load_json_file(path):
    if not path or not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)

def load_data(data_dir):
    files = ["departments", "budget_cycles", "categories", "budget_lines", "budget_months", "vendors", "subscriptions"]
    data = {}
    for f in files:
        path = os.path.join(data_dir, f"{f}.json")
        data[f] = load_json_file(path) if os.path.exists(path) else []
    return data

def build_user_prompt(agent, department, today, data, forecast_summary, prior_outputs):
    d = data
    base = f"Department: {department}\nToday: {today}\n\n"

    if agent == "renewal_risk":
        return base + f"Subscriptions:\n{json.dumps(d['subscriptions'], indent=2)}\n\nVendors:\n{json.dumps(d['vendors'], indent=2)}\n\nReturn JSON only."

    if agent == "run_rate_forecast":
        return base + f"Pre-computed forecast summary (do not recalculate):\n{json.dumps(forecast_summary, indent=2)}\n\nCategories:\n{json.dumps(d['categories'], indent=2)}\n\nBudget lines:\n{json.dumps(d['budget_lines'], indent=2)}\n\nReturn JSON only."

    if agent == "anomaly_detect":
        return base + f"Budget lines:\n{json.dumps(d['budget_lines'], indent=2)}\n\nBudget months:\n{json.dumps(d['budget_months'], indent=2)}\n\nSubscriptions:\n{json.dumps(d['subscriptions'], indent=2)}\n\nReturn JSON only."

    if agent == "consolidation_suggest":
        return base + f"Subscriptions:\n{json.dumps(d['subscriptions'], indent=2)}\n\nBudget lines:\n{json.dumps(d['budget_lines'], indent=2)}\n\nVendors:\n{json.dumps(d['vendors'], indent=2)}\n\nReturn JSON only."

    if agent == "orchestrator":
        return base + f"""Inputs:
Budget lines: {json.dumps(d['budget_lines'], indent=2)}
Budget months: {json.dumps(d['budget_months'], indent=2)}
Subscriptions: {json.dumps(d['subscriptions'], indent=2)}
Forecast summary: {json.dumps(forecast_summary, indent=2)}

Specialist outputs:
renewal_risk: {json.dumps(prior_outputs.get('renewal_risk', {}), indent=2)}
run_rate_forecast: {json.dumps(prior_outputs.get('run_rate_forecast', {}), indent=2)}
anomaly_detect: {json.dumps(prior_outputs.get('anomaly_detect', {}), indent=2)}
consolidation_suggest: {json.dumps(prior_outputs.get('consolidation_suggest', {}), indent=2)}

Merge into one brief and action queue. Return JSON only."""

    if agent == "narrative_brief":
        return base + f"Input brief:\n{json.dumps(prior_outputs.get('orchestrator', {}), indent=2)}\n\nReturn JSON with bullets, paragraph, top_actions. JSON only."

    if agent == "html_dashboard_builder":
        return base + f"Brief data:\n{json.dumps(prior_outputs.get('orchestrator', {}), indent=2)}\n\nNarrative:\n{json.dumps(prior_outputs.get('narrative_brief', {}), indent=2)}\n\nReturn complete HTML file only."

    return base + "Return JSON only."

def call_lm_studio(system_prompt, user_prompt, retry_suffix=""):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt + (f"\n\n{retry_suffix}" if retry_suffix else "")}
    ]
    payload = json.dumps({
        "model": MODEL,
        "messages": messages,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
    }).encode("utf-8")

    req = urllib.request.Request(
        LM_STUDIO_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"ERROR: {e}"

def strip_fences(text):
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def validate_json(text, required_keys):
    text = strip_fences(text)
    try:
        parsed = json.loads(text)
        if required_keys:
            missing = [k for k in required_keys if k not in parsed]
            if missing:
                return None, f"Missing keys: {missing}"
        return parsed, None
    except Exception as e:
        return None, str(e)

def run_agent(agent, department, today, data_dir, forecast_summary_path, prior_outputs_dir, output_path):
    data = load_data(data_dir)
    forecast_summary = load_json_file(forecast_summary_path)

    prior_outputs = {}
    if prior_outputs_dir:
        for name in AGENT_SCHEMAS:
            p = os.path.join(prior_outputs_dir, f"{name}.json")
            if os.path.exists(p):
                prior_outputs[name] = load_json_file(p)

    system_prompt = SYSTEM_PROMPTS[agent]
    user_prompt = build_user_prompt(agent, department, today, data, forecast_summary, prior_outputs)
    required_keys = AGENT_SCHEMAS.get(agent)

    print(f"Calling LM Studio for agent: {agent}...")
    raw = call_lm_studio(system_prompt, user_prompt)

    if raw.startswith("ERROR:"):
        print(f"LM Studio call failed: {raw}")
        result = {"error": raw, "agent": agent}
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        return False

    if agent == "html_dashboard_builder":
        # HTML output — write directly
        content = raw.strip()
        if not content.startswith("<!DOCTYPE"):
            # Try to extract HTML
            if "<!DOCTYPE" in content:
                content = content[content.index("<!DOCTYPE"):]
        with open(output_path.replace(".json", ".html"), "w") as f:
            f.write(content)
        print(f"HTML dashboard written to: {output_path.replace('.json', '.html')}")
        return True

    parsed, error = validate_json(raw, required_keys)
    if parsed is None:
        print(f"Validation failed ({error}). Retrying...")
        retry_suffix = "Return only raw JSON with no markdown formatting, no code fences, no explanation."
        raw2 = call_lm_studio(system_prompt, user_prompt, retry_suffix)
        parsed, error2 = validate_json(raw2, required_keys)
        if parsed is None:
            print(f"Retry also failed ({error2}). Writing error object.")
            parsed = {"error": f"First: {error}. Retry: {error2}", "agent": agent, "raw_preview": raw[:200]}

    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(parsed, f, indent=2)
    print(f"Output written to: {output_path}")
    return "error" not in parsed

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a SpendOps agent against LM Studio")
    parser.add_argument("--agent", required=True, choices=list(AGENT_SCHEMAS.keys()))
    parser.add_argument("--department", required=True)
    parser.add_argument("--today", default=date.today().strftime("%Y-%m-%d"))
    parser.add_argument("--data-dir", default="./data/")
    parser.add_argument("--forecast-summary", default="./outputs/forecast_summary.json")
    parser.add_argument("--prior-outputs-dir", default="./outputs/")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    ok = run_agent(args.agent, args.department, args.today, args.data_dir, args.forecast_summary, args.prior_outputs_dir, args.output)
    exit(0 if ok else 1)
