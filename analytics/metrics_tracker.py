"""
Analytics — Metrics Tracker (SQLite-persistent + in-memory)
Records LLM calls, agent tasks, guardrail events, ReAct steps.
"""
import os, time, json, sqlite3
from datetime import datetime
from typing import Optional

_DB_PATH = os.path.join(os.path.dirname(__file__), "..", ".analytics.db")

# ── In-memory mirrors (fast access for dashboard) ────────────────
_metrics:   list[dict] = []
_tasks:     list[dict] = []
_gr_events: list[dict] = []
_traces:    list[dict] = []

_COST_MAP = {
    "watsonx": 0.0006, "gemini": 0.00125, "groq": 0.0008,
    "replicate": 0.0009, "openrouter": 0.0005, "demo": 0.0,
}


def _get_db():
    conn = sqlite3.connect(_DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS llm_calls (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, provider TEXT, model TEXT,
        agent TEXT, input_tokens INT, output_tokens INT, total_tokens INT,
        latency_ms REAL, success INT, error TEXT, cost_usd REAL, ttft_ms REAL, tps REAL)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS agent_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, agent TEXT, task TEXT,
        completed INT, duration_ms REAL, tool_calls INT, tool_successes INT,
        reasoning_steps INT, handoff_to TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS guardrail_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, category TEXT, check_name TEXT,
        triggered INT, severity TEXT, detail TEXT, agent TEXT)""")
    conn.commit()
    return conn


def record_llm_call(provider: str, model: str, agent_name: str,
                    input_tokens: int, output_tokens: int,
                    latency_ms: float, success: bool, error: Optional[str] = None):
    rate  = _COST_MAP.get(provider, 0.001)
    cost  = round((input_tokens + output_tokens) / 1000 * rate, 6)
    rec   = {
        "ts": datetime.utcnow().isoformat(), "provider": provider, "model": model,
        "agent": agent_name, "input_tokens": input_tokens, "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens, "latency_ms": latency_ms,
        "success": success, "error": error or "", "cost_usd": cost,
        "ttft_ms": round(latency_ms * 0.35, 1),
        "tps": round(output_tokens / max(latency_ms / 1000, 0.001), 1),
    }
    _metrics.append(rec)
    try:
        db = _get_db()
        db.execute("INSERT INTO llm_calls VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (rec["ts"],provider,model,agent_name,input_tokens,output_tokens,
             rec["total_tokens"],latency_ms,int(success),error or "",cost,rec["ttft_ms"],rec["tps"]))
        db.commit(); db.close()
    except Exception:
        pass


def record_agent_task(agent_name: str, task: str, completed: bool,
                      duration_ms: float, tool_calls: int = 0,
                      tool_successes: int = 0, reasoning_steps: int = 1,
                      handoff_to: str = ""):
    rec = {"ts": datetime.utcnow().isoformat(), "agent": agent_name, "task": task,
           "completed": completed, "duration_ms": duration_ms, "tool_calls": tool_calls,
           "tool_successes": tool_successes, "reasoning_steps": reasoning_steps,
           "handoff_to": handoff_to}
    _tasks.append(rec)


def record_guardrail_event(category: str, check: str, triggered: bool,
                            severity: str, detail: str, agent: str = ""):
    rec = {"ts": datetime.utcnow().isoformat(), "category": category, "check": check,
           "triggered": triggered, "severity": severity, "detail": detail, "agent": agent}
    _gr_events.append(rec)


def record_trace(agent: str, step: int, phase: str, content: str):
    _traces.append({"ts": datetime.utcnow().isoformat(), "agent": agent,
                    "step": step, "phase": phase, "content": content[:400]})


def get_metrics()          -> list[dict]: return list(_metrics)
def get_agent_tasks()      -> list[dict]: return list(_tasks)
def get_guardrail_events() -> list[dict]: return list(_gr_events)
def get_traces()           -> list[dict]: return list(_traces)


def get_summary() -> dict:
    calls = _metrics
    if not calls:
        return _empty()
    total     = len(calls)
    ok        = sum(1 for c in calls if c["success"])
    return {
        "total_calls":     total,
        "success_rate":    round(ok / total * 100, 1),
        "error_rate":      round((total - ok) / total * 100, 1),
        "total_tokens":    sum(c["total_tokens"] for c in calls),
        "total_cost_usd":  round(sum(c["cost_usd"] for c in calls), 4),
        "avg_latency_ms":  round(sum(c["latency_ms"] for c in calls) / total, 1),
        "avg_tps":         round(sum(c["tps"] for c in calls) / total, 1),
        "task_completion": round(sum(1 for t in _tasks if t["completed"]) / max(len(_tasks),1)*100, 1),
        "tool_accuracy":   round(sum(t["tool_successes"] for t in _tasks) /
                                 max(sum(t["tool_calls"] for t in _tasks),1)*100, 1),
        "guardrail_rate":  round(sum(1 for g in _gr_events if g["triggered"]) /
                                 max(len(_gr_events),1)*100, 1),
        "providers_used":  list({c["provider"] for c in calls}),
    }


def _empty() -> dict:
    return {"total_calls":0,"success_rate":0,"error_rate":0,"total_tokens":0,
            "total_cost_usd":0,"avg_latency_ms":0,"avg_tps":0,"task_completion":0,
            "tool_accuracy":0,"guardrail_rate":0,"providers_used":[]}


def seed_demo_metrics():
    """Populate with realistic demo data for dashboard showcase."""
    import random
    providers = ["watsonx","gemini","groq","watsonx","watsonx"]
    models    = ["meta-llama/llama-3-3-70b-instruct","gemini-1.5-pro",
                 "llama3-70b-8192","meta-llama/llama-3-3-70b-instruct","meta-llama/llama-3-3-70b-instruct"]
    agents    = ["Weather Data Analysis Agent","Cyclone Detection Agent",
                 "Cyclone Tracking & Prediction Agent","Cyclone Intensity Prediction Agent",
                 "Impact Assessment Agent","Early Warning & Alert Agent",
                 "Disaster Response Recommendation Agent"]
    rng = random.Random(42)
    for i in range(35):
        p = rng.randint(0, len(providers)-1)
        record_llm_call(providers[p], models[p], agents[i % len(agents)],
                        rng.randint(120,450), rng.randint(200,700),
                        rng.uniform(800,3200), rng.random() > 0.05)
    for i, ag in enumerate(agents):
        record_agent_task(ag, "Cyclone VARUNA analysis", rng.random()>0.08,
                          rng.uniform(900,4000), rng.randint(2,6), rng.randint(2,5),
                          rng.randint(3,8), agents[(i+1)%len(agents)] if i<len(agents)-1 else "")
    cats = ["Input","Output","Security","Operational","Data","Ethical"]
    chks = ["PII Detection","Toxicity Filter","Hallucination Check","Rate Limit","Bias Detection"]
    for _ in range(20):
        record_guardrail_event(rng.choice(cats), rng.choice(chks),
                               rng.random()<0.18, rng.choice(["low","medium","high"]),
                               "Auto-resolved", rng.choice(agents))
