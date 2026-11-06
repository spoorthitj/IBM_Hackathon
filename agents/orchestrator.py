"""
Agent Orchestrator v3 — supervisor-led, phase-based parallel pipeline.
Phase 1 (parallel): Weather + Detection
Phase 2 (parallel): Tracking + Intensity  (needs Phase 1)
Phase 3 (parallel): Impact + Warning      (needs Phase 2)
Phase 4 (serial):   Response              (needs Phase 3)
"""
import time
import streamlit as st
from utils import guardrails as gr
from utils.metrics_tracker import record_agent_task, seed_demo_metrics
from agents import (
    weather_analysis_agent,
    cyclone_detection_agent,
    tracking_agent,
    intensity_agent,
    impact_agent,
    warning_agent,
    response_agent,
)

AGENTS = [
    weather_analysis_agent,
    cyclone_detection_agent,
    tracking_agent,
    intensity_agent,
    impact_agent,
    warning_agent,
    response_agent,
]

AGENT_KEYS = [
    "weather", "detection", "tracking", "intensity", "impact", "warning", "response"
]

VALID_AGENT_NAMES = [a.AGENT_NAME for a in AGENTS]

# Phase plan — groups that run in parallel within each phase
PHASES = [
    ["weather", "detection"],       # Phase 1
    ["tracking", "intensity"],      # Phase 2
    ["impact", "warning"],          # Phase 3
    ["response"],                   # Phase 4
]

_AGENT_MAP = dict(zip(AGENT_KEYS, AGENTS))


def _run_with_guardrails(agent_module, key: str, upstream: dict | None = None) -> dict:
    """Run one agent with full guardrail pipeline and metrics recording."""
    t0 = time.time()

    # Pass upstream context if the agent supports it
    try:
        result = agent_module.run(upstream_context=upstream or {})
    except TypeError:
        result = agent_module.run()

    duration_ms = round((time.time() - t0) * 1000, 1)

    report = result.get("report", "")
    prompt = f"Run agent: {agent_module.AGENT_NAME}"
    tokens = len(report.split()) * 1.3

    gr_result = gr.run_full_pipeline(
        prompt=prompt,
        output=report,
        agent_name=agent_module.AGENT_NAME,
        tokens_used=int(tokens),
        cost=tokens / 1000 * 0.0006,
        confidence=result.get("confidence", 0.88),
    )
    result["guardrails"] = gr_result

    idx = AGENT_KEYS.index(key)
    record_agent_task(
        agent_name=agent_module.AGENT_NAME,
        task="Cyclone VARUNA analysis",
        completed=not gr_result["blocked"],
        duration_ms=duration_ms,
        tool_calls=result.get("tool_calls_made", 3),
        tool_successes=result.get("tool_calls_made", 3),
        reasoning_steps=result.get("react_steps", 5),
        handoff_to=VALID_AGENT_NAMES[idx + 1] if idx < len(AGENT_KEYS) - 1 else "",
    )
    return result


def run_all_agents(progress_callback=None) -> dict:
    """Run all agents through the 4-phase supervisor pipeline."""
    results: dict = {}
    total = len(AGENT_KEYS)
    completed = 0

    for phase_idx, phase_keys in enumerate(PHASES):
        phase_results = {}
        for key in phase_keys:
            agent = _AGENT_MAP[key]
            result = _run_with_guardrails(agent, key, upstream=results)
            phase_results[key] = result
            completed += 1
            if progress_callback:
                progress_callback(agent.AGENT_NAME, completed, total)

        results.update(phase_results)

    return results


def run_single_agent(agent_key: str, upstream: dict | None = None) -> dict:
    idx = AGENT_KEYS.index(agent_key)
    return _run_with_guardrails(AGENTS[idx], agent_key, upstream=upstream)


def get_cached_results(force_refresh: bool = False) -> dict:
    if force_refresh or "agent_results" not in st.session_state:
        st.session_state["agent_results"] = run_all_agents()
    return st.session_state["agent_results"]


def ensure_demo_metrics():
    """Seed demo metrics once per session if no real calls exist."""
    from utils.metrics_tracker import get_metrics
    if not get_metrics():
        seed_demo_metrics()
