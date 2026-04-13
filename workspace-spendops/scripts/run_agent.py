#!/usr/bin/env python3
"""
SpendOps - Agent runner
Calls the selected AI backend (OpenRouter or LM Studio) with the correct system + user prompt
for each specialist agent. Validates JSON output. Retries once on failure.

Usage:
  python3 scripts/run_agent.py --agent renewal_risk --department "IT/OT" --today 2026-03-05 \
    --data-dir ./data/ --forecast-summary ./outputs/forecast_summary.json \
    --output ./outputs/renewal_risk.json [--ai-backend openrouter|lmstudio]
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import date

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
except ImportError:
    pass

# --- OpenRouter config ---
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Fast, cheap model for structured JSON agents (renewal, forecast, anomaly)
OPENROUTER_MODEL_FAST  = os.environ.get("OPENROUTER_MODEL_FAST",  "google/gemini-2.0-flash-001")
# Smarter model for reasoning/synthesis agents (consolidation, orchestrator, narrative)
OPENROUTER_MODEL_SMART = os.environ.get("OPENROUTER_MODEL_SMART", "anthropic/claude-3-5-haiku")

# Per-agent model routing — override via .env (OPENROUTER_MODEL_FAST / OPENROUTER_MODEL_SMART)
AGENT_MODELS = {
    "renewal_risk":           OPENROUTER_MODEL_FAST,
    "run_rate_forecast":      OPENROUTER_MODEL_FAST,
    "anomaly_detect":         OPENROUTER_MODEL_FAST,
    "consolidation_suggest":  OPENROUTER_MODEL_SMART,   # needs reasoning for accurate recs
    "orchestrator":           OPENROUTER_MODEL_SMART,
    "narrative_brief":        OPENROUTER_MODEL_SMART,   # needs coherent prose
    "html_dashboard_builder": OPENROUTER_MODEL_FAST,
}

# --- LM Studio config (legacy local fallback) ---
LM_STUDIO_URL = "http://127.0.0.1:1234/v1/chat/completions"
LM_STUDIO_MODEL = "lfm2-8b-a1b"
TEMPERATURE = 0.1
MAX_TOKENS = 8192

AGENT_SCHEMAS = {
    "renewal_risk": ["renewals_next_30_days", "renewals_next_60_days", "renewals_next_90_days", "risks_ranked", "missing_data", "suggested_actions"],
    "run_rate_forecast": ["department", "cycle", "budget_total", "actual_ytd", "forecast_eoy_rolling", "forecast_eoy_blended", "variance_vs_budget"],
    "anomaly_detect": ["anomalies"],  # each item must have: severity, category, message, dollar_impact
    "consolidation_suggest": ["candidates"],  # prompt now enforces this key explicitly
    "orchestrator": ["department", "cycle", "kpis", "renewals", "top_risks", "action_queue"],
    "narrative_brief": ["summary_bullets", "summary_paragraph", "top_actions"],
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
Rank anomalies by severity and dollar impact. Include evidence ids.

Return a JSON object with exactly this structure:
{
  "anomalies": [
    {
      "severity": "high|medium|low",
      "category": "Short category label (e.g. 'AWS Cloud Overspend', 'Unowned Renewal', 'Forecast vs Plan Variance')",
      "message": "Full explanation of the anomaly with vendor name, dollar amounts, and the specific data that triggered it.",
      "delta": <number — actual minus planned, can be negative>,
      "dollar_impact": <positive integer — total dollar exposure>,
      "follow_up_questions": ["question 1", "question 2"]
    }
  ]
}

Rules:
- category must be a short descriptive label (3–6 words), NOT the word "Anomaly"
- message must cite specific vendor names, dollar amounts, and dates from the data
- dollar_impact must be a concrete integer, not a range
- Return JSON only. No prose before or after.""",

    "consolidation_suggest": """You are the SpendOps Consolidation Suggestion Agent. Identify overlap, redundant subscriptions, and consolidation opportunities based ONLY on the contracts provided.

CRITICAL: Only reference contracts that actually exist in the input data. Do NOT invent contracts or vendors not present in the data.

Return a JSON object with exactly this structure — the top-level key MUST be "candidates":
{
  "candidates": [
    {
      "title": "Short action title (e.g. Consolidate Network Monitoring)",
      "type": "consolidate|cancel|evaluate",
      "description": "Why this is an opportunity, referencing actual vendor names and costs.",
      "annual_savings": <integer dollar amount>,
      "savings_label": "$X,XXX/yr",
      "vendors": [
        {"name": "VendorName", "annual_cost": <integer>, "action": "Keep|Cancel|Evaluate"}
      ],
      "deadline": "YYYY-MM-DD or descriptive date",
      "deadline_label": "Human readable deadline"
    }
  ]
}

Rules:
- annual_savings must be a concrete number from the actual contract costs, not a range
- If no consolidation opportunity exists, return {"candidates": []}
- Do not recommend cancelling a contract that is not in the input subscription list
- Return JSON only. No prose before or after.""",

    "orchestrator": """You are the SpendOps Orchestrator. Merge specialist agent outputs into one spend brief and prioritized action queue for a department leader.
Do not invent data. Rank items by urgency and financial impact.
Prioritize: renewals within 90 days, missing ownership, forecast over-budget risk, anomalies, consolidation candidates.
Never modify budget numbers. Include evidence ids for every item.
If any specialist returned an error, include it in the notes array and continue.
Return JSON only. No prose before or after the JSON block.""",

    "narrative_brief": """You are the SpendOps Narrative Agent. Convert structured JSON brief data into a sharp, numbers-first leadership summary.

STRICT RULES — every field must cite real data:
- summary_bullets: 4–5 bullets. EACH bullet must contain at least one specific: dollar amount, vendor name, date, or % variance. No generic phrases ("action required", "needs attention") without a concrete number or name attached.
  Examples of GOOD bullets:
    "CrowdStrike ($65K) and ServiceNow ($36K) renewals are unowned — combined $101K at risk by Apr 19"
    "AWS Cloud & Infrastructure tracking $25K over plan YTD; EOY forecast exceeds budget by $103K (11.4%)"
  Examples of BAD bullets (do NOT write these):
    "Immediate action is required on several contracts."
    "Budget variance needs to be addressed."
- summary_paragraph: 2–3 sentences. Name the top 2–3 risks by vendor + dollar amount. State the total budget variance dollar amount and percentage. Mention the forecast EOY figure.
- top_actions: exactly 3 strings. Each must name a specific vendor, dollar amount, or deadline. No vague verbs.

Return ONLY this exact JSON structure — no wrapper keys, no markdown:
{
  "summary_bullets": ["bullet with numbers", "bullet with numbers", "bullet with numbers", "bullet with numbers"],
  "summary_paragraph": "2-3 sentence paragraph naming vendors and dollar amounts",
  "top_actions": ["specific action 1 with vendor/amount", "specific action 2", "specific action 3"]
}""",

    "html_dashboard_builder": """You are the SpendOps HTML Dashboard Builder. Produce a single self-contained HTML file.
Requirements: dark theme, professional design. KPI cards, renewal risk table, anomaly cards, consolidation cards, bar chart.
Populate all data from the brief JSON. Include a Last Updated timestamp.
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


def slim_budget_months(months):
    """Return only rows with actual_amount or precomputed_forecast set — drops empty future rows.
    Also drops null fields to cut tokens further."""
    out = []
    for m in months:
        if m.get("actual_amount") or m.get("precomputed_forecast"):
            out.append({k: v for k, v in m.items() if v is not None})
    return out


def slim_budget_lines(lines):
    """Drop null fields from budget lines."""
    return [{k: v for k, v in l.items() if v is not None} for l in lines]


def build_user_prompt(agent, department, today, data, forecast_summary, prior_outputs):
    d = data
    base = f"Department: {department}\nToday: {today}\n\n"

    if agent == "renewal_risk":
        return base + f"Subscriptions:\n{json.dumps(d['subscriptions'])}\n\nVendors:\n{json.dumps(d['vendors'])}\n\nReturn JSON only."

    if agent == "run_rate_forecast":
        return base + f"Pre-computed forecast summary (do not recalculate):\n{json.dumps(forecast_summary)}\n\nCategories:\n{json.dumps(d['categories'])}\n\nBudget lines:\n{json.dumps(slim_budget_lines(d['budget_lines']))}\n\nReturn JSON only."

    if agent == "anomaly_detect":
        # Slim budget_months to only rows with actual data — cuts tokens by ~70%
        months_slim = slim_budget_months(d['budget_months'])
        return base + f"Budget lines:\n{json.dumps(slim_budget_lines(d['budget_lines']))}\n\nBudget months (actuals + forecasts only):\n{json.dumps(months_slim)}\n\nSubscriptions:\n{json.dumps(d['subscriptions'])}\n\nReturn JSON only."

    if agent == "consolidation_suggest":
        return base + f"Subscriptions:\n{json.dumps(d['subscriptions'])}\n\nBudget lines:\n{json.dumps(slim_budget_lines(d['budget_lines']))}\n\nVendors:\n{json.dumps(d['vendors'])}\n\nReturn JSON only."

    if agent == "orchestrator":
        # Orchestrator only needs specialist outputs + forecast summary — no raw DB rows needed
        return base + f"""Forecast summary: {json.dumps(forecast_summary)}

Specialist outputs:
renewal_risk: {json.dumps(prior_outputs.get('renewal_risk', {}))}
run_rate_forecast: {json.dumps(prior_outputs.get('run_rate_forecast', {}))}
anomaly_detect: {json.dumps(prior_outputs.get('anomaly_detect', {}))}
consolidation_suggest: {json.dumps(prior_outputs.get('consolidation_suggest', {}))}

Merge into one brief and action queue. Return JSON only."""

    if agent == "narrative_brief":
        return base + f"Input brief:\n{json.dumps(prior_outputs.get('orchestrator', {}), indent=2)}\n\nReturn JSON with bullets, paragraph, top_actions. JSON only."

    if agent == "html_dashboard_builder":
        return base + f"Brief data:\n{json.dumps(prior_outputs.get('orchestrator', {}), indent=2)}\n\nNarrative:\n{json.dumps(prior_outputs.get('narrative_brief', {}), indent=2)}\n\nReturn complete HTML file only."

    return base + "Return JSON only."


def call_openrouter(system_prompt, user_prompt, retry_suffix="", model=None):
    """Call OpenRouter API using the openai-compatible SDK."""
    if not OPENROUTER_API_KEY:
        return "ERROR: OPENROUTER_API_KEY not set. Copy .env.example to .env and add your key."
    if model is None:
        model = OPENROUTER_MODEL_FAST
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
        )
        full_user = user_prompt + (f"\n\n{retry_suffix}" if retry_suffix else "")
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": full_user},
            ],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            extra_headers={"X-Title": "SpendOps"},
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"ERROR: {e}"


def call_lm_studio(system_prompt, user_prompt, retry_suffix=""):
    """Call local LM Studio instance (legacy fallback)."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt + (f"\n\n{retry_suffix}" if retry_suffix else "")}
    ]
    payload = json.dumps({
        "model": LM_STUDIO_MODEL,
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
            if "choices" not in result:
                return f"ERROR: no choices in response. Full response: {json.dumps(result)[:300]}"
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
                print(f"  NOTE: Expected keys not present: {missing} (accepting anyway)")
        return parsed, None
    except Exception as e:
        return None, str(e)


def run_agent(agent, department, today, data_dir, forecast_summary_path, prior_outputs_dir, output_path, ai_backend="openrouter"):
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

    model = AGENT_MODELS.get(agent, OPENROUTER_MODEL_FAST)
    print(f"[{ai_backend}:{model}] Running agent: {agent}...")

    if ai_backend == "openrouter":
        raw = call_openrouter(system_prompt, user_prompt, model=model)
    else:
        raw = call_lm_studio(system_prompt, user_prompt)

    if raw.startswith("ERROR:"):
        print(f"AI call failed: {raw}")
        result = {"error": raw, "agent": agent}
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
        return False

    if agent == "html_dashboard_builder":
        content = raw.strip()
        if not content.startswith("<!DOCTYPE"):
            if "<!DOCTYPE" in content:
                content = content[content.index("<!DOCTYPE"):]
        html_path = output_path.replace(".json", ".html")
        with open(html_path, "w") as f:
            f.write(content)
        print(f"HTML dashboard written to: {html_path}")
        return True

    parsed, error = validate_json(raw, required_keys)
    if parsed is None:
        print(f"Validation failed ({error}). Retrying...")
        retry_suffix = "Return only raw JSON with no markdown formatting, no code fences, no explanation."
        if ai_backend == "openrouter":
            raw2 = call_openrouter(system_prompt, user_prompt, retry_suffix, model=model)
        else:
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
    parser = argparse.ArgumentParser(description="Run a SpendOps agent")
    parser.add_argument("--agent", required=True, choices=list(AGENT_SCHEMAS.keys()))
    parser.add_argument("--department", required=True)
    parser.add_argument("--today", default=date.today().strftime("%Y-%m-%d"))
    parser.add_argument("--data-dir", default="./data/")
    parser.add_argument("--forecast-summary", default="./outputs/forecast_summary.json")
    parser.add_argument("--prior-outputs-dir", default="./outputs/")
    parser.add_argument("--output", required=True)
    parser.add_argument("--ai-backend", choices=["openrouter", "lmstudio"], default="openrouter")
    args = parser.parse_args()
    ok = run_agent(
        args.agent, args.department, args.today,
        args.data_dir, args.forecast_summary, args.prior_outputs_dir,
        args.output, args.ai_backend
    )
    exit(0 if ok else 1)
