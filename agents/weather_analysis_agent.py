"""
Agent 1: Weather Data Analysis Agent
LLM: IBM Granite (watsonx) | Architecture: ReAct
"""
from core.llm_router import generate_for_agent
from core.react_engine import run_react_loop
from core.prompt_optimizer import optimize
from memory.short_term import store, recall
from memory.vector_store import query_as_context, store_agent_output
from analytics.metrics_tracker import record_agent_task
import time

AGENT_NAME = "Weather Data Analysis Agent"
AGENT_ICON = "🌡️"
AGENT_LLM  = "IBM Granite (watsonx)"
AGENT_DESC = "Analyzes SST, pressure, wind, humidity, and rainfall for cyclogenesis signatures."
AGENT_TOOLS = ["weather_fetch", "get_sst", "pressure_trend"]


def run(upstream: dict | None = None) -> dict:
    from data_layer.data_generator import generate_meteorological_data
    import pandas as pd

    df     = generate_meteorological_data(hours_back=24)
    latest = df.iloc[-1]
    trend_p = df["pressure_hpa"].iloc[-1] - df["pressure_hpa"].iloc[0]
    trend_w = df["wind_speed_kmh"].iloc[-1] - df["wind_speed_kmh"].iloc[0]

    # Long-term memory context
    lt_ctx = query_as_context("cyclone formation meteorological conditions")
    st_ctx = recall(AGENT_NAME)

    goal    = "Analyze current meteorological data and assess cyclogenesis potential"
    context = f"""OBSERVATIONS:
SST:{latest['sea_surface_temp']}°C | Pressure:{latest['pressure_hpa']}hPa (trend:{trend_p:+.1f}) |
Wind:{latest['wind_speed_kmh']}km/h (trend:{trend_w:+.1f}) | Humidity:{latest['humidity_pct']}% |
Rainfall:{latest['rainfall_mm']}mm | Cloud:{latest['cloud_cover_pct']}% | Pos:{latest['lat']}N,{latest['lon']}E
DOMAIN KNOWLEDGE: {lt_ctx}
PRIOR CONTEXT: {st_ctx}"""

    t0 = time.time()
    llm_fn = lambda p: generate_for_agent(AGENT_NAME, p)
    report, steps = run_react_loop(AGENT_NAME, goal, context, llm_fn, max_iter=2)

    # Store to memory
    store(AGENT_NAME, "weather_analysis", report[:500])
    store_agent_output(AGENT_NAME, "latest", report)

    dur   = round((time.time() - t0) * 1000, 1)
    sev   = "HIGH" if latest["pressure_hpa"] < 990 else ("MODERATE" if latest["pressure_hpa"] < 1000 else "LOW")
    record_agent_task(AGENT_NAME, goal, True, dur, len(AGENT_TOOLS), len(AGENT_TOOLS),
                      len(steps), "Cyclone Detection Agent")

    return {
        "agent_name": AGENT_NAME, "icon": AGENT_ICON, "llm": AGENT_LLM,
        "report": report, "data": df, "status": sev, "react_steps": [s.to_dict() for s in steps],
        "metrics": {
            "SST": f"{latest['sea_surface_temp']} °C",
            "Pressure": f"{latest['pressure_hpa']} hPa",
            "Wind Speed": f"{latest['wind_speed_kmh']} km/h",
            "Humidity": f"{latest['humidity_pct']} %",
            "Rainfall": f"{latest['rainfall_mm']} mm/hr",
        }
    }
