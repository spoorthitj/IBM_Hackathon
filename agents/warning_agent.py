"""
Agent 6: Early Warning & Alert Agent
LLM: Groq (LLaMA 3) | Architecture: ReAct
"""
from core.llm_router import generate_for_agent
from core.react_engine import run_react_loop
from memory.short_term import store, recall
from memory.vector_store import query_as_context, store_agent_output
from analytics.metrics_tracker import record_agent_task
from datetime import datetime, timedelta
import time

AGENT_NAME  = "Early Warning & Alert Agent"
AGENT_ICON  = "🚨"
AGENT_LLM   = "Groq (LLaMA 3)"
AGENT_DESC  = "Generates location-specific colour-coded alerts and preparedness recommendations."
AGENT_TOOLS = ["dispatch_alert", "ndrf_status"]

ALERT_LEVELS = {
    "CRITICAL": {"label":"RED ALERT",    "icon":"🔴","color":"#880E4F"},
    "HIGH":     {"label":"ORANGE ALERT", "icon":"🟠","color":"#B71C1C"},
    "MODERATE": {"label":"YELLOW ALERT", "icon":"🟡","color":"#E65100"},
    "LOW":      {"label":"GREEN ADVISORY","icon":"🟢","color":"#1B5E20"},
}


def run(upstream: dict | None = None) -> dict:
    from data_layer.data_generator import generate_impact_assessment

    impacts  = generate_impact_assessment()
    lt_ctx   = query_as_context("IMD cyclone warning protocol evacuation alert")
    st_ctx   = recall(AGENT_NAME)
    up_ctx   = ""
    if upstream and "impact" in upstream:
        up_ctx = upstream["impact"].get("report","")[:200]

    issued = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
    city_summary = "\n".join(
        f"{ALERT_LEVELS[c['risk_level']]['icon']} {c['city']} — {c['risk_level']} | surge:{c['surge_risk']}% wind:{c['wind_risk']}%"
        for c in impacts[:5])

    goal    = "Generate official colour-coded early warnings and preparedness bulletins"
    context = f"""ISSUED: {issued} UTC | CYCLONE: VARUNA
CITY RISK STATUS:\n{city_summary}
IMPACT CONTEXT: {up_ctx}  DOMAIN: {lt_ctx}  MEMORY: {st_ctx}"""

    t0 = time.time()
    llm_fn = lambda p: generate_for_agent(AGENT_NAME, p)
    report, steps = run_react_loop(AGENT_NAME, goal, context, llm_fn, max_iter=2)

    store(AGENT_NAME, "warning_bulletin", report[:500])
    store_agent_output(AGENT_NAME, "latest", report)

    city_alerts = [{"city": c["city"], "state": c["state"],
                    **ALERT_LEVELS[c["risk_level"]], "risk": c["overall_risk"],
                    "risk_level": c["risk_level"]} for c in impacts]
    top_al = ALERT_LEVELS[impacts[0]["risk_level"]]
    dur    = round((time.time()-t0)*1000, 1)
    record_agent_task(AGENT_NAME, goal, True, dur, len(AGENT_TOOLS), len(AGENT_TOOLS),
                      len(steps), "Disaster Response Recommendation Agent")

    return {
        "agent_name": AGENT_NAME, "icon": AGENT_ICON, "llm": AGENT_LLM,
        "report": report, "city_alerts": city_alerts, "issued_at": issued,
        "status": top_al["label"], "status_color": top_al["color"],
        "react_steps": [s.to_dict() for s in steps],
        "metrics": {
            "Alert Issued": issued,
            "Cyclone Name": "VARUNA",
            "Highest Alert": top_al["label"],
            "Districts Alerted": str(len(city_alerts)),
            "Next Update": (datetime.utcnow()+timedelta(hours=3)).strftime("%H:%M UTC"),
        }
    }
