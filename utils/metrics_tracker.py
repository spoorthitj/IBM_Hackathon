"""
LLM & Agent Performance Metrics Tracker.
Stores per-call metrics in st.session_state for the evaluation dashboard.
Thread-safe append-only design; no external DB needed.
"""
import time
from datetime import datetime
from typing import Optional
import random

# ── In-memory store (populated via session_state in app context) ─
_metrics: list[dict] = []

# ── Per-agent task tracking ──────────────────────────────────────
_agent_tasks: list[dict] = []

# ── Guardrail events ─────────────────────────────────────────────
_guardrail_events: list[dict] = []


def record_llm_call(
    provider: str,
    model: str,
    agent_name: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: float,
    success: bool,
    error: Optional[str] = None,
):
    """Append one LLM call record."""
    # Estimate cost (rough $/1k-token rates)
    cost_map = {
        "watsonx":  0.0006,
        "gemini":   0.00125,
        "groq":     0.0008,
        "replicate":0.0009,
        "demo":     0.0,
    }
    rate = cost_map.get(provider, 0.001)
    cost = round((input_tokens + output_tokens) / 1000 * rate, 6)

    _metrics.append({
        "ts":            datetime.utcnow().isoformat(),
        "provider":      provider,
        "model":         model,
        "agent":         agent_name,
        "input_tokens":  input_tokens,
        "output_tokens": output_tokens,
        "total_tokens":  input_tokens + output_tokens,
        "latency_ms":    latency_ms,
        "success":       success,
        "error":         error or "",
        "cost_usd":      cost,
        "ttft_ms":       round(latency_ms * 0.35, 1),   # estimated TTFT
        "tps":           round(output_tokens / max(latency_ms / 1000, 0.001), 1),
    })


def record_agent_task(
    agent_name: str,
    task: str,
    completed: bool,
    duration_ms: float,
    tool_calls: int = 0,
    tool_successes: int = 0,
    reasoning_steps: int = 1,
    handoff_to: Optional[str] = None,
):
    _agent_tasks.append({
        "ts":             datetime.utcnow().isoformat(),
        "agent":          agent_name,
        "task":           task,
        "completed":      completed,
        "duration_ms":    duration_ms,
        "tool_calls":     tool_calls,
        "tool_successes": tool_successes,
        "reasoning_steps":reasoning_steps,
        "handoff_to":     handoff_to or "",
    })


def record_guardrail_event(
    category: str,
    check: str,
    triggered: bool,
    severity: str,
    detail: str,
    agent: str = "",
):
    _guardrail_events.append({
        "ts":       datetime.utcnow().isoformat(),
        "category": category,
        "check":    check,
        "triggered":triggered,
        "severity": severity,
        "detail":   detail,
        "agent":    agent,
    })


def get_metrics()         -> list[dict]: return list(_metrics)
def get_agent_tasks()     -> list[dict]: return list(_agent_tasks)
def get_guardrail_events()-> list[dict]: return list(_guardrail_events)


def get_summary() -> dict:
    """Aggregated summary for dashboard KPIs."""
    calls = _metrics
    if not calls:
        return _empty_summary()

    total     = len(calls)
    successes = sum(1 for c in calls if c["success"])
    total_tok = sum(c["total_tokens"] for c in calls)
    total_cost= sum(c["cost_usd"]     for c in calls)
    avg_lat   = sum(c["latency_ms"]   for c in calls) / total
    avg_tps   = sum(c["tps"]          for c in calls) / total
    err_rate  = round((total - successes) / total * 100, 1)

    tasks = _agent_tasks
    tcr   = round(sum(1 for t in tasks if t["completed"]) / max(len(tasks),1) * 100, 1)
    tool_acc = round(
        sum(t["tool_successes"] for t in tasks) /
        max(sum(t["tool_calls"] for t in tasks), 1) * 100, 1)

    gr_events = _guardrail_events
    gr_triggered = sum(1 for g in gr_events if g["triggered"])
    gr_rate      = round(gr_triggered / max(len(gr_events), 1) * 100, 1)

    return {
        "total_calls":     total,
        "success_rate":    round(successes / total * 100, 1),
        "error_rate":      err_rate,
        "total_tokens":    total_tok,
        "total_cost_usd":  round(total_cost, 4),
        "avg_latency_ms":  round(avg_lat, 1),
        "avg_tps":         round(avg_tps, 1),
        "task_completion": tcr,
        "tool_accuracy":   tool_acc,
        "guardrail_rate":  gr_rate,
        "providers_used":  list({c["provider"] for c in calls}),
    }


def _empty_summary() -> dict:
    return {
        "total_calls":0,"success_rate":0,"error_rate":0,
        "total_tokens":0,"total_cost_usd":0,"avg_latency_ms":0,
        "avg_tps":0,"task_completion":0,"tool_accuracy":0,
        "guardrail_rate":0,"providers_used":[],
    }


def seed_demo_metrics():
    """Populate with realistic demo data for dashboard showcase."""
    import math
    providers = ["watsonx","gemini","groq","watsonx","watsonx"]
    models    = [
        "meta-llama/llama-3-3-70b-instruct",
        "gemini-1.5-pro",
        "llama3-70b-8192",
        "meta-llama/llama-3-3-70b-instruct",
        "meta-llama/llama-3-3-70b-instruct",
    ]
    agents = [
        "Weather Data Analysis Agent",
        "Cyclone Detection Agent",
        "Cyclone Tracking & Prediction Agent",
        "Cyclone Intensity Prediction Agent",
        "Impact Assessment Agent",
        "Early Warning & Alert Agent",
        "Disaster Response Recommendation Agent",
    ]

    rng = random.Random(42)
    for i in range(35):
        p_idx = rng.randint(0, len(providers)-1)
        prov  = providers[p_idx]
        model = models[p_idx]
        agent = agents[i % len(agents)]
        lat   = rng.uniform(800, 3200)
        in_t  = rng.randint(120, 450)
        out_t = rng.randint(200, 700)
        ok    = rng.random() > 0.05   # 5% error rate
        cost_map = {"watsonx":0.0006,"gemini":0.00125,"groq":0.0008,"replicate":0.0009,"demo":0.0}
        rate  = cost_map.get(prov, 0.001)
        _metrics.append({
            "ts":           datetime.utcnow().isoformat(),
            "provider":     prov,
            "model":        model,
            "agent":        agent,
            "input_tokens": in_t,
            "output_tokens":out_t,
            "total_tokens": in_t + out_t,
            "latency_ms":   round(lat,1),
            "success":      ok,
            "error":        "" if ok else "timeout",
            "cost_usd":     round((in_t+out_t)/1000*rate, 6),
            "ttft_ms":      round(lat*0.35, 1),
            "tps":          round(out_t / max(lat/1000,0.001), 1),
        })

    for i, ag in enumerate(agents):
        _agent_tasks.append({
            "ts": datetime.utcnow().isoformat(), "agent": ag,
            "task": f"Cyclone VARUNA analysis — run {i+1}",
            "completed": rng.random() > 0.08,
            "duration_ms": rng.uniform(900, 4000),
            "tool_calls": rng.randint(2, 6),
            "tool_successes": rng.randint(2, 5),
            "reasoning_steps": rng.randint(3, 8),
            "handoff_to": agents[(i+1) % len(agents)] if i < len(agents)-1 else "",
        })

    categories = ["Input","Output","Security","Operational","Data","Ethical"]
    checks     = ["PII Detection","Toxicity Filter","Hallucination Check",
                  "Rate Limit","Token Budget","Bias Detection","Injection Guard"]
    for _ in range(20):
        _guardrail_events.append({
            "ts": datetime.utcnow().isoformat(),
            "category": rng.choice(categories),
            "check":    rng.choice(checks),
            "triggered":rng.random() < 0.18,
            "severity": rng.choice(["low","medium","high"]),
            "detail":   "Auto-detected and resolved",
            "agent":    rng.choice(agents),
        })
