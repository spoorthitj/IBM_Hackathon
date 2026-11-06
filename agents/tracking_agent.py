"""
Agent 3: Cyclone Tracking & Prediction Agent
LLM: Google Gemini | Architecture: ReAct
"""
from core.llm_router import generate_for_agent
from core.react_engine import run_react_loop
from memory.short_term import store, recall
from memory.vector_store import query_as_context, store_agent_output
from analytics.metrics_tracker import record_agent_task
import time

AGENT_NAME  = "Cyclone Tracking & Prediction Agent"
AGENT_ICON  = "📡"
AGENT_LLM   = "Google Gemini"
AGENT_DESC  = "Predicts cyclone movement, direction, speed, and landfall using NWP ensemble models."
AGENT_TOOLS = ["get_track", "satellite_imagery"]


def run(upstream: dict | None = None) -> dict:
    from data_layer.data_generator import generate_cyclone_track
    import pandas as pd

    track_df = generate_cyclone_track(n_points=20)
    cur      = track_df.loc[track_df["hours_offset"].abs().idxmin()]
    fore     = track_df[track_df["is_forecast"]].head(5)
    fc_text  = "\n".join(
        f"+{int(r['hours_offset'])}h | {r['lat']}N {r['lon']}E | {r['wind_speed_kts']}kts | {r['intensity']}"
        for _, r in fore.iterrows())

    lt_ctx = query_as_context("cyclone track NWP ensemble landfall prediction")
    st_ctx = recall(AGENT_NAME)
    up_ctx = ""
    if upstream and "detection" in upstream:
        up_ctx = upstream["detection"].get("report","")[:200]

    goal    = "Predict cyclone track, landfall location, timing, and cone of uncertainty"
    context = f"""CURRENT: {cur['lat']}N,{cur['lon']}E | {cur['intensity']} | {cur['wind_speed_kts']}kts | {cur['pressure_hpa']}hPa
FORECAST TRACK:\n{fc_text}
DETECTION: {up_ctx}  DOMAIN: {lt_ctx}  MEMORY: {st_ctx}"""

    t0 = time.time()
    llm_fn = lambda p: generate_for_agent(AGENT_NAME, p)
    report, steps = run_react_loop(AGENT_NAME, goal, context, llm_fn, max_iter=2)

    store(AGENT_NAME, "track_forecast", report[:500])
    store_agent_output(AGENT_NAME, "latest", report)

    near = track_df[track_df["hours_offset"] >= 0].head(1)
    eta  = f"+{int(near.iloc[0]['hours_offset'])}h" if not near.empty else "—"
    dur  = round((time.time()-t0)*1000, 1)
    record_agent_task(AGENT_NAME, goal, True, dur, len(AGENT_TOOLS), len(AGENT_TOOLS),
                      len(steps), "Cyclone Intensity Prediction Agent")

    return {
        "agent_name": AGENT_NAME, "icon": AGENT_ICON, "llm": AGENT_LLM,
        "report": report, "track_data": track_df,
        "status": cur["intensity"], "status_color": cur["color"],
        "react_steps": [s.to_dict() for s in steps],
        "metrics": {
            "Current Position": f"{cur['lat']}°N, {cur['lon']}°E",
            "Current Intensity": cur["intensity"],
            "Wind Speed": f"{cur['wind_speed_kts']} kts",
            "Landfall ETA": eta,
            "Landfall Area": "Visakhapatnam–Puri",
        }
    }
