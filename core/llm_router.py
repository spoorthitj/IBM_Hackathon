"""
Core — Per-Agent LLM Router
Maps each agent to its dedicated LLM provider.
Falls back through the chain if the assigned provider is unavailable.
"""
from gateway.llm_client import generate_with, available_providers

# ── Agent → Provider assignment ───────────────────────────────────
AGENT_LLM_MAP = {
    "Weather Data Analysis Agent":          "watsonx",   # IBM Granite
    "Cyclone Detection Agent":              "watsonx",   # IBM Granite
    "Cyclone Tracking & Prediction Agent":  "gemini",    # Google Gemini
    "Cyclone Intensity Prediction Agent":   "groq",      # Groq LLaMA 3
    "Impact Assessment Agent":              "gemini",    # Google Gemini
    "Early Warning & Alert Agent":          "groq",      # Groq LLaMA 3
    "Disaster Response Recommendation Agent": "watsonx", # IBM Granite
    "Supervisor Agent":                     "watsonx",   # IBM Granite (orchestrator)
}

# Fallback chain if assigned provider unavailable
_FALLBACK_CHAIN = ["watsonx", "gemini", "groq", "openrouter", "replicate"]


def get_provider_for_agent(agent_name: str) -> str:
    """Return the assigned provider for an agent (with availability fallback)."""
    assigned = AGENT_LLM_MAP.get(agent_name, "watsonx")
    avail    = available_providers()
    if assigned in avail:
        return assigned
    for fb in _FALLBACK_CHAIN:
        if fb in avail:
            return fb
    return "demo"


def generate_for_agent(agent_name: str, prompt: str) -> str:
    """Generate text using the agent's assigned LLM."""
    provider = get_provider_for_agent(agent_name)
    return generate_with(provider, prompt, agent_name)


def get_agent_llm_info() -> list[dict]:
    """Return info about each agent's LLM assignment for display."""
    avail = available_providers()
    info  = []
    for agent, assigned in AGENT_LLM_MAP.items():
        actual  = get_provider_for_agent(agent)
        info.append({
            "agent":    agent,
            "assigned": assigned,
            "actual":   actual,
            "online":   assigned in avail,
            "fallback": actual != assigned,
        })
    return info
