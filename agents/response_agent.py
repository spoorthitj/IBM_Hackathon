"""
Agent 7: Disaster Response Recommendation Agent
LLM: IBM Granite (watsonx) | Architecture: ReAct
"""
from core.llm_router import generate_for_agent
from core.react_engine import run_react_loop
from memory.short_term import store, recall
from memory.vector_store import query_as_context, store_agent_output
from analytics.metrics_tracker import record_agent_task
import time

AGENT_NAME  = "Disaster Response Recommendation Agent"
AGENT_ICON  = "🛡️"
AGENT_LLM   = "IBM Granite (watsonx)"
AGENT_DESC  = "Suggests evacuation planning, resource allocation, shelter ID, and response strategies."
AGENT_TOOLS = ["shelter_lookup", "ndrf_status", "dispatch_alert"]

NDRF_TEAMS = [
    {"location":"Visakhapatnam","teams":4,"personnel":240,"status":"Deployed"},
    {"location":"Bhubaneswar",  "teams":3,"personnel":180,"status":"Deployed"},
    {"location":"Chennai",      "teams":2,"personnel":120,"status":"Standby"},
    {"location":"Rajahmundry",  "teams":2,"personnel":120,"status":"Deployed"},
    {"location":"Kolkata",      "teams":1,"personnel": 60,"status":"Standby"},
]
SHELTERS = [
    {"district":"Srikakulam",   "count":62,"capacity":180000},
    {"district":"Visakhapatnam","count":58,"capacity":145000},
    {"district":"Vizianagaram", "count":41,"capacity":100000},
    {"district":"Ganjam",       "count":72,"capacity":220000},
    {"district":"Puri",         "count":55,"capacity":165000},
]


def run(upstream: dict | None = None) -> dict:
    from data_layer.data_generator import generate_impact_assessment

    impacts  = generate_impact_assessment()
    lt_ctx   = query_as_context("NDRF evacuation disaster response cyclone preparedness")
    st_ctx   = recall(AGENT_NAME)
    up_ctx   = ""
    if upstream and "warning" in upstream:
        up_ctx = upstream["warning"].get("report","")[:200]

    high_risk = [c for c in impacts if c["risk_level"] in ("CRITICAL","HIGH")]
    pop_risk  = round(sum(c["pop_M"] for c in high_risk), 1)
    ndrf_txt  = " | ".join(f"{t['location']}:{t['teams']}teams({t['status']})" for t in NDRF_TEAMS)
    sh_txt    = " | ".join(f"{s['district']}:{s['count']}shelters({s['capacity']//1000}k)" for s in SHELTERS)

    goal    = "Generate comprehensive disaster response plan with evacuation, resources, and SAR strategy"
    context = f"""POPULATION AT RISK: {pop_risk}M | CITIES: {','.join(c['city'] for c in high_risk[:4])}
NDRF: {ndrf_txt}
SHELTERS: {sh_txt}
WARNING CONTEXT: {up_ctx}  DOMAIN: {lt_ctx}  MEMORY: {st_ctx}"""

    t0 = time.time()
    llm_fn = lambda p: generate_for_agent(AGENT_NAME, p)
    report, steps = run_react_loop(AGENT_NAME, goal, context, llm_fn, max_iter=2)

    store(AGENT_NAME, "response_plan", report[:500])
    store_agent_output(AGENT_NAME, "latest", report)

    dur = round((time.time()-t0)*1000, 1)
    record_agent_task(AGENT_NAME, goal, True, dur, len(AGENT_TOOLS), len(AGENT_TOOLS),
                      len(steps), "")

    return {
        "agent_name": AGENT_NAME, "icon": AGENT_ICON, "llm": AGENT_LLM,
        "report": report, "ndrf_teams": NDRF_TEAMS, "shelters": SHELTERS,
        "status": "ACTIVE", "status_color": "#880E4F",
        "react_steps": [s.to_dict() for s in steps],
        "metrics": {
            "NDRF Teams": str(sum(t["teams"] for t in NDRF_TEAMS)),
            "Total Personnel": str(sum(t["personnel"] for t in NDRF_TEAMS)),
            "Cyclone Shelters": str(sum(s["count"] for s in SHELTERS)),
            "Shelter Capacity": f"{sum(s['capacity'] for s in SHELTERS):,}",
            "Response Status": "ACTIVE",
        }
    }
