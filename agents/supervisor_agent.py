"""
Supervisor Agent — Hierarchical Architecture
Decides which agents to run, in what order, and coordinates the pipeline.
Architecture: Hierarchical with Parallel Phase execution.
"""
import time
from core.llm_router import generate_for_agent
from memory.short_term import store, recall
from analytics.metrics_tracker import record_agent_task

AGENT_NAME = "Supervisor Agent"
AGENT_ICON = "🎯"
AGENT_LLM  = "IBM Granite (watsonx)"

# Phase-based parallel execution plan
PIPELINE_PHASES = [
    {
        "phase": 1,
        "name": "Data Collection",
        "agents": ["weather", "detection"],
        "parallel": True,
        "description": "Collect and analyze raw data simultaneously",
    },
    {
        "phase": 2,
        "name": "Prediction",
        "agents": ["tracking", "intensity"],
        "parallel": True,
        "description": "Run track and intensity predictions in parallel",
    },
    {
        "phase": 3,
        "name": "Assessment & Response",
        "agents": ["impact", "warning", "response"],
        "parallel": False,
        "description": "Sequential: impact feeds warning feeds response",
    },
]


def plan(situation: str) -> dict:
    """Supervisor decides the execution plan based on situation severity."""
    t0 = time.time()

    lt_ctx = recall(AGENT_NAME)
    prompt = f"""You are the Supervisor Agent for the Indian Cyclone Detection & Early Warning System.

CURRENT SITUATION: {situation}

AVAILABLE AGENTS:
1. Weather Data Analysis (IBM Granite) — meteorological data analysis
2. Cyclone Detection (IBM Granite) — satellite imagery and cyclone identification
3. Cyclone Tracking & Prediction (Gemini) — track and landfall prediction
4. Cyclone Intensity Prediction (Groq) — RI and intensity forecast
5. Impact Assessment (Gemini) — population and infrastructure risk
6. Early Warning & Alert (Groq) — colour-coded alerts
7. Disaster Response (IBM Granite) — evacuation and response plans

TASK: As supervisor, decide:
1. Which agents are most critical for this situation (rank by priority)
2. Justify why each selected agent is needed
3. Identify any agents that can be skipped given the situation
4. Provide overall coordination instructions for the agent pipeline

Be concise and decisive. Output a structured coordination plan."""

    report = generate_for_agent(AGENT_NAME, prompt)
    store(AGENT_NAME, "supervision_plan", report[:500])
    dur = round((time.time()-t0)*1000, 1)
    record_agent_task(AGENT_NAME, "Create agent execution plan", True, dur,
                      0, 0, 3, "Weather Data Analysis Agent")

    return {
        "agent_name": AGENT_NAME,
        "icon":       AGENT_ICON,
        "llm":        AGENT_LLM,
        "report":     report,
        "phases":     PIPELINE_PHASES,
        "status":     "COORDINATING",
    }


def get_architecture_info() -> dict:
    """Return architecture metadata for display."""
    return {
        "type":        "Hierarchical + Parallel Phases",
        "phases":       len(PIPELINE_PHASES),
        "total_agents": sum(len(p["agents"]) for p in PIPELINE_PHASES),
        "parallel_phases": sum(1 for p in PIPELINE_PHASES if p["parallel"]),
        "supervisor_llm": AGENT_LLM,
        "description": (
            "Phase 1 (Parallel): Weather + Detection simultaneously. "
            "Phase 2 (Parallel): Tracking + Intensity simultaneously. "
            "Phase 3 (Sequential): Impact → Warning → Response (each reads upstream output)."
        ),
    }
