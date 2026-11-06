"""Tools — Satellite & Track Tools"""
from tools.registry import register_tool

def _get_satellite(query: str) -> str:
    return ("INSAT-3D imagery: Cloud spiral score 0.78, 4 convective bands detected, "
            "Circulation centre confirmed at 10.2°N 87.6°E, Dvorak T3.0")

def _get_track(query: str) -> str:
    return ("NWP ensemble track: System NNW at 14 km/h. "
            "Landfall Visakhapatnam–Puri corridor in +48h. "
            "Track confidence HIGH for 24h, MODERATE for 48h.")

def _get_intensity_forecast(query: str) -> str:
    return ("Intensity forecast: +24h 75kts (Very Severe), "
            "+48h 95kts (Extremely Severe), +72h 65kts (Weakening post-landfall). "
            "RI probability: 68%")

def register():
    register_tool("satellite_imagery",   _get_satellite,         "Get INSAT satellite imagery analysis",  "satellite")
    register_tool("get_track",           _get_track,             "Get NWP ensemble cyclone track forecast","tracking")
    register_tool("intensity_forecast",  _get_intensity_forecast,"Get cyclone intensity forecast",         "intensity")
