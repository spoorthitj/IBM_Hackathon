"""
Tools — Registry & MCP Adapter
Central registry for all agent tools.
"""
_REGISTRY: dict[str, dict] = {}


def register_tool(name: str, fn, description: str, category: str = "general"):
    _REGISTRY[name] = {"fn": fn, "description": description, "category": category}


def get_tool(name: str):
    entry = _REGISTRY.get(name.strip().lower())
    return entry["fn"] if entry else None


def list_tools() -> list[dict]:
    return [{"name": k, "description": v["description"], "category": v["category"]}
            for k, v in _REGISTRY.items()]


# ── Auto-register all tools on import ────────────────────────────
def _auto_register():
    from tools import weather_tools, satellite_tools, impact_tools, alert_tools
    weather_tools.register()
    satellite_tools.register()
    impact_tools.register()
    alert_tools.register()


_auto_register()
