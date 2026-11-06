"""Tools — Alert & Response Tools"""
from tools.registry import register_tool
from datetime import datetime

_ALERT_LOG: list[dict] = []

def _dispatch_alert(message: str) -> str:
    _ALERT_LOG.append({"ts": datetime.utcnow().isoformat(), "message": message[:300]})
    return f"ALERT DISPATCHED at {datetime.utcnow().strftime('%H:%M UTC')}: {message[:100]}..."

def _get_ndrf_status(query: str) -> str:
    return ("NDRF status: Visakhapatnam 4 teams (240 personnel) DEPLOYED, "
            "Bhubaneswar 3 teams (180) DEPLOYED, Rajahmundry 2 teams (120) DEPLOYED. "
            "Total: 12 teams, 720 personnel pre-positioned.")

def _get_alert_log() -> list[dict]:
    return list(_ALERT_LOG)

def register():
    register_tool("dispatch_alert", _dispatch_alert, "Dispatch cyclone alert to authorities", "alert")
    register_tool("ndrf_status",    _get_ndrf_status,"Get NDRF team deployment status",       "alert")
