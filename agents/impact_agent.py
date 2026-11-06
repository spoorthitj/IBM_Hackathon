"""
Agent 5: Impact Assessment Agent
LLM: Google Gemini | Architecture: ReAct
"""
from core.llm_router import generate_for_agent
from core.react_engine import run_react_loop
from memory.short_term import store, recall
from memory.vector_store import query_as_context, store_agent_output
from analytics.metrics_tracker import record_agent_task
import time

AGENT_NAME  = "Impact Assessment Agent"
AGENT_ICON  = "🗺️"
AGENT_LLM   = "Google Gemini"
AGENT_DESC  = "Assesses risks to population, infrastructure, agriculture, and essential services."
AGENT_TOOLS = ["get_population", "shelter_lookup", "infrastructure_risk"]


def run(upstream: dict | None = None) -> dict:
    from data_layer.data_generator import generate_impact_assessment, generate_cyclone_track

    impacts  = generate_impact_assessment()
    track_df = generate_cyclone_track(n_points=20)
    lt_ctx   = query_as_context("storm surge impact population coastal vulnerability")
    st_ctx   = recall(AGENT_NAME)
    up_ctx   = ""
    if upstream and "intensity" in upstream:
        up_ctx = upstream["intensity"].get("report","")[:200]

    high_risk = [c for c in impacts if c["risk_level"] in ("CRITICAL","HIGH")]
    top3      = "\n".join(f"{c['city']},{c['state']} | {c['risk_level']} | {c['overall_risk']}% | {c['pop_M']}M"
                          for c in impacts[:3])

    goal    = "Assess cyclone impact on coastal population, infrastructure, and agriculture"
    context = f"""TOP RISK CITIES:\n{top3}
INTENSITY CONTEXT: {up_ctx}
DOMAIN: {lt_ctx}  MEMORY: {st_ctx}"""

    t0 = time.time()
    llm_fn = lambda p: generate_for_agent(AGENT_NAME, p)
    report, steps = run_react_loop(AGENT_NAME, goal, context, llm_fn, max_iter=2)

    store(AGENT_NAME, "impact_assessment", report[:500])
    store_agent_output(AGENT_NAME, "latest", report)

    total_pop = round(sum(c["pop_M"] for c in high_risk), 1)
    dur = round((time.time()-t0)*1000, 1)
    record_agent_task(AGENT_NAME, goal, True, dur, len(AGENT_TOOLS), len(AGENT_TOOLS),
                      len(steps), "Early Warning & Alert Agent")

    return {
        "agent_name": AGENT_NAME, "icon": AGENT_ICON, "llm": AGENT_LLM,
        "report": report, "impact_data": impacts,
        "status": impacts[0]["risk_level"] if impacts else "LOW",
        "status_color": "#E53935",
        "react_steps": [s.to_dict() for s in steps],
        "metrics": {
            "High/Critical Cities": str(len(high_risk)),
            "Population at Risk": f"{total_pop} M",
            "Highest Risk City": impacts[0]["city"] if impacts else "—",
            "Max Storm Surge": "3–5 m",
            "Expected Rainfall": "200–300 mm",
        }
    }
