"""Tools — Weather Data Tools"""
from tools.registry import register_tool
from data_layer.data_generator import generate_meteorological_data

def _fetch_weather(query: str) -> str:
    df = generate_meteorological_data(hours_back=6)
    r  = df.iloc[-1]
    return (f"SST:{r['sea_surface_temp']}°C Pressure:{r['pressure_hpa']}hPa "
            f"Wind:{r['wind_speed_kmh']}km/h Humidity:{r['humidity_pct']}% "
            f"Rainfall:{r['rainfall_mm']}mm Lat:{r['lat']}N Lon:{r['lon']}E")

def _get_sst(query: str) -> str:
    df = generate_meteorological_data(hours_back=1)
    return f"Current SST: {df.iloc[-1]['sea_surface_temp']}°C (Bay of Bengal, system centre)"

def _get_pressure_trend(query: str) -> str:
    df = generate_meteorological_data(hours_back=24)
    trend = df["pressure_hpa"].iloc[-1] - df["pressure_hpa"].iloc[0]
    return f"Pressure trend (24h): {trend:+.1f} hPa. Current: {df.iloc[-1]['pressure_hpa']} hPa"

def register():
    register_tool("weather_fetch",   _fetch_weather,     "Fetch current meteorological observations", "weather")
    register_tool("get_sst",         _get_sst,           "Get current sea surface temperature",       "weather")
    register_tool("pressure_trend",  _get_pressure_trend,"Get 24h atmospheric pressure trend",        "weather")
