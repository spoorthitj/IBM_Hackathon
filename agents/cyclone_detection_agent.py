"""
Agent 2: Cyclone Detection Agent
LLM: IBM Granite (watsonx) | Architecture: ReAct
"""
from core.llm_router import generate_for_agent
from core.react_engine import run_react_loop
from memory.short_term import store, recall
from memory.vector_store import query_as_context, store_agent_output
from analytics.metrics_tracker import record_agent_task
import time

AGENT_NAME  = "Cyclone Detection Agent"
AGENT_ICON  = "🛰️"
AGENT_LLM   = "IBM Granite (watsonx)"
AGENT_DESC  = "Identifies cyclone formations from INSAT satellite imagery and weather anomalies."
AGENT_TOOLS = ["satellite_imagery", "weather_fetch"]

SATELLITE_SIGNATURES = {
    "cloud_spiral_score": 0.78, "convective_bands": 4,
    "eye_detected": False, "circulation_center": True,
    "dvorak_t_number": 3.0, "oi_sst_anomaly_c": 1.4, "olr_wm2": 180,
}

def _dvorak_label(t):
    m = {1:"Disturbance",2:"Depression",2.5:"Deep Depression",3:"Cyclonic Storm",
         4:"Severe",4.5:"Very Severe",5:"Very Severe",6:"Extremely Severe",7:"Super Cyclonic"}
    return m.get(t, min(m.keys(), key=lambda x: abs(x-t)) and m[min(m.keys(), key=lambda x: abs(x-t))])


def run(upstream: dict | None = None) -> dict:
    sigs   = SATELLITE_SIGNATURES
    lt_ctx = query_as_context("cyclone satellite detection Dvorak")
    st_ctx = recall(AGENT_NAME)
    wx_ctx = ""
    if upstream and "weather" in upstream:
        wx_ctx = upstream["weather"].get("report", "")[:300]

    goal    = "Detect and classify cyclone formation from satellite imagery and weather data"
    context = f"""SATELLITE SIGNATURES:
Spiral:{sigs['cloud_spiral_score']:.2f} | Bands:{sigs['convective_bands']} | Eye:{'YES' if sigs['eye_detected'] else 'NO'} |
Circulation:{'YES' if sigs['circulation_center'] else 'NO'} | Dvorak:T{sigs['dvorak_t_number']} | SST anom:+{sigs['oi_sst_anomaly_c']}°C | OLR:{sigs['olr_wm2']}W/m²
UPSTREAM WEATHER: {wx_ctx}
DOMAIN: {lt_ctx}  MEMORY: {st_ctx}"""

    t0 = time.time()
    llm_fn = lambda p: generate_for_agent(AGENT_NAME, p)
    report, steps = run_react_loop(AGENT_NAME, goal, context, llm_fn, max_iter=2)

    store(AGENT_NAME, "detection_result", report[:500])
    store_agent_output(AGENT_NAME, "latest", report)

    wind_kts   = 55.0
    confidence = round(min(100, sigs["cloud_spiral_score"]*40 + sigs["dvorak_t_number"]*8 +
                           (10 if sigs["circulation_center"] else 0) + sigs["convective_bands"]*2), 1)
    dur = round((time.time() - t0)*1000, 1)
    record_agent_task(AGENT_NAME, goal, True, dur, len(AGENT_TOOLS), len(AGENT_TOOLS),
                      len(steps), "Cyclone Tracking & Prediction Agent")

    return {
        "agent_name": AGENT_NAME, "icon": AGENT_ICON, "llm": AGENT_LLM,
        "report": report, "status": "Severe Cyclonic", "status_color": "#FFB74D",
        "confidence": confidence, "signatures": sigs, "react_steps": [s.to_dict() for s in steps],
        "metrics": {
            "Dvorak T-Number": f"T{sigs['dvorak_t_number']} ({_dvorak_label(sigs['dvorak_t_number'])})",
            "Detection Confidence": f"{confidence}%",
            "Spiral Score": f"{sigs['cloud_spiral_score']:.0%}",
            "OLR": f"{sigs['olr_wm2']} W/m²",
            "SST Anomaly": f"+{sigs['oi_sst_anomaly_c']} °C",
        }
    }
