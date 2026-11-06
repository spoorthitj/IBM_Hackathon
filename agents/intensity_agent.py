"""
Agent 4: Cyclone Intensity Prediction Agent
LLM: Groq (LLaMA 3) | Architecture: ReAct
"""
from core.llm_router import generate_for_agent
from core.react_engine import run_react_loop
from memory.short_term import store, recall
from memory.vector_store import query_as_context, store_agent_output
from analytics.metrics_tracker import record_agent_task
import numpy as np, time

AGENT_NAME  = "Cyclone Intensity Prediction Agent"
AGENT_ICON  = "⚡"
AGENT_LLM   = "Groq (LLaMA 3)"
AGENT_DESC  = "Estimates intensity and Rapid Intensification probability using SHIPS-style predictors."
AGENT_TOOLS = ["intensity_forecast", "get_sst"]

ENV = {"sst_c":29.8,"heat_content_kjcm2":95,"shear_ms":7.2,"humidity_700hpa":72,
       "divergence_200hpa":1.8e-5,"mpi_kts":155,"current_ws_kts":55,"24h_change_kts":18}


def _ri_prob(p) -> float:
    s = 0.0
    if p["sst_c"]>=29: s+=25
    elif p["sst_c"]>=28: s+=15
    if p["shear_ms"]<=5: s+=25
    elif p["shear_ms"]<=10: s+=15
    if p["heat_content_kjcm2"]>=80: s+=20
    if p["humidity_700hpa"]>=70: s+=15
    if p["current_ws_kts"]<100: s+=10
    if p["24h_change_kts"]>=15: s+=10
    return min(100, round(s,1))


def run(upstream: dict | None = None) -> dict:
    from data_layer.data_generator import get_intensity_label

    ri    = _ri_prob(ENV)
    fc    = []
    ws    = ENV["current_ws_kts"]
    rng   = np.random.default_rng(7)
    for h in [12,24,36,48,72]:
        ws = min(160, ws + 6 + (ri/100)*10 if h<=24 else ws - 2) + rng.normal(0,1)
        it = get_intensity_label(ws)
        fc.append({"hour":h,"wind_kts":round(ws,1),"intensity":it["label"],"color":it["color"]})

    lt_ctx = query_as_context("rapid intensification SST wind shear cyclone intensity")
    st_ctx = recall(AGENT_NAME)
    up_ctx = ""
    if upstream and "tracking" in upstream:
        up_ctx = upstream["tracking"].get("report","")[:200]

    goal    = "Predict cyclone intensity evolution and assess Rapid Intensification probability"
    context = f"""ENV: SST:{ENV['sst_c']}°C OHC:{ENV['heat_content_kjcm2']}kJ/cm² Shear:{ENV['shear_ms']}m/s Humidity:{ENV['humidity_700hpa']}%
Current:{ENV['current_ws_kts']}kts +24h_change:+{ENV['24h_change_kts']}kts MPI:{ENV['mpi_kts']}kts RI_prob:{ri}%
FORECAST: {' | '.join(f"+{f['hour']}h:{f['wind_kts']}kts({f['intensity']})" for f in fc)}
TRACKING: {up_ctx}  DOMAIN: {lt_ctx}  MEMORY: {st_ctx}"""

    t0 = time.time()
    llm_fn = lambda p: generate_for_agent(AGENT_NAME, p)
    report, steps = run_react_loop(AGENT_NAME, goal, context, llm_fn, max_iter=2)

    store(AGENT_NAME, "intensity_forecast", report[:500])
    store_agent_output(AGENT_NAME, "latest", report)

    cur_int = get_intensity_label(ENV["current_ws_kts"])
    dur     = round((time.time()-t0)*1000, 1)
    record_agent_task(AGENT_NAME, goal, True, dur, len(AGENT_TOOLS), len(AGENT_TOOLS),
                      len(steps), "Impact Assessment Agent")

    return {
        "agent_name": AGENT_NAME, "icon": AGENT_ICON, "llm": AGENT_LLM,
        "report": report, "forecast": fc, "env_params": ENV, "ri_prob": ri,
        "status": cur_int["label"], "status_color": cur_int["color"],
        "react_steps": [s.to_dict() for s in steps],
        "metrics": {
            "Current Intensity": f"{ENV['current_ws_kts']} kts ({cur_int['label']})",
            "RI Probability": f"{ri}%",
            "RI Alert": "HIGH" if ri>=60 else ("MODERATE" if ri>=40 else "LOW"),
            "Peak Forecast": f"{max(f['wind_kts'] for f in fc)} kts",
            "MPI": f"{ENV['mpi_kts']} kts",
        }
    }
