"""
Mock meteorological data generator simulating real IMD/NOAA-style datasets.
Used when live API keys are not configured.
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

# ------------------------------------------------------------------
# Seed for reproducibility across a single session
# ------------------------------------------------------------------
_RNG = np.random.default_rng(42)


# ------------------------------------------------------------------
# Indian coastal bounding boxes
# ------------------------------------------------------------------
BAY_OF_BENGAL_REGION = {"lat_min": 5.0, "lat_max": 22.0, "lon_min": 80.0, "lon_max": 100.0}
ARABIAN_SEA_REGION   = {"lat_min": 5.0, "lat_max": 25.0, "lon_min": 55.0, "lon_max": 78.0}

# Key coastal cities with (lat, lon, population_millions)
COASTAL_CITIES = [
    {"name": "Chennai",       "lat": 13.08, "lon": 80.27, "pop_M": 10.9, "state": "Tamil Nadu"},
    {"name": "Visakhapatnam","lat": 17.69, "lon": 83.22, "pop_M": 2.0,  "state": "Andhra Pradesh"},
    {"name": "Kolkata",       "lat": 22.57, "lon": 88.36, "pop_M": 14.8, "state": "West Bengal"},
    {"name": "Paradip",       "lat": 20.32, "lon": 86.61, "pop_M": 0.3,  "state": "Odisha"},
    {"name": "Puri",          "lat": 19.81, "lon": 85.83, "pop_M": 0.2,  "state": "Odisha"},
    {"name": "Mumbai",        "lat": 19.08, "lon": 72.88, "pop_M": 20.7, "state": "Maharashtra"},
    {"name": "Surat",         "lat": 21.17, "lon": 72.83, "pop_M": 6.1,  "state": "Gujarat"},
    {"name": "Porbandar",     "lat": 21.64, "lon": 69.61, "pop_M": 0.3,  "state": "Gujarat"},
    {"name": "Thiruvananthapuram","lat": 8.52, "lon": 76.94,"pop_M": 1.7, "state": "Kerala"},
    {"name": "Mangaluru",     "lat": 12.91, "lon": 74.86, "pop_M": 0.6,  "state": "Karnataka"},
]

CYCLONE_INTENSITY_SCALE = [
    {"label": "Depression",        "min_ws": 17, "max_ws": 27,  "color": "#4FC3F7"},
    {"label": "Deep Depression",   "min_ws": 28, "max_ws": 33,  "color": "#29B6F6"},
    {"label": "Cyclonic Storm",    "min_ws": 34, "max_ws": 47,  "color": "#FFF176"},
    {"label": "Severe Cyclonic",   "min_ws": 48, "max_ws": 63,  "color": "#FFB74D"},
    {"label": "Very Severe",       "min_ws": 64, "max_ws": 89,  "color": "#FF7043"},
    {"label": "Extremely Severe",  "min_ws": 90, "max_ws": 119, "color": "#E53935"},
    {"label": "Super Cyclonic",    "min_ws": 120,"max_ws": 200, "color": "#880E4F"},
]


def get_intensity_label(wind_speed_knots: float) -> dict:
    for level in CYCLONE_INTENSITY_SCALE:
        if level["min_ws"] <= wind_speed_knots <= level["max_ws"]:
            return level
    if wind_speed_knots < 17:
        return {"label": "Low Pressure Area", "min_ws": 0, "max_ws": 16, "color": "#B0BEC5"}
    return CYCLONE_INTENSITY_SCALE[-1]


def generate_meteorological_data(hours_back: int = 24) -> pd.DataFrame:
    """Generate time-series meteorological data for Bay of Bengal grid."""
    now = datetime.utcnow()
    timestamps = [now - timedelta(hours=i) for i in range(hours_back, 0, -1)]

    # Simulate a developing cyclone scenario
    base_pressure = 1005
    records = []
    for i, ts in enumerate(timestamps):
        progress = i / hours_back
        records.append({
            "timestamp":         ts,
            "sea_surface_temp":  round(28.5 + 1.5 * progress + _RNG.normal(0, 0.3), 2),
            "pressure_hpa":      round(base_pressure - 25 * progress + _RNG.normal(0, 1.5), 1),
            "wind_speed_kmh":    round(20 + 80 * progress + _RNG.normal(0, 3), 1),
            "wind_direction_deg":round(200 + 30 * np.sin(2 * np.pi * progress) + _RNG.normal(0, 5), 1),
            "humidity_pct":      round(min(100, 65 + 30 * progress + _RNG.normal(0, 2)), 1),
            "rainfall_mm":       round(max(0, 5 + 50 * progress**1.5 + _RNG.normal(0, 2)), 1),
            "cloud_cover_pct":   round(min(100, 40 + 55 * progress + _RNG.normal(0, 3)), 1),
            "lat":               round(BAY_OF_BENGAL_REGION["lat_min"] + 5 + progress * 8 + _RNG.normal(0, 0.1), 3),
            "lon":               round(BAY_OF_BENGAL_REGION["lon_min"] + 10 - progress * 5 + _RNG.normal(0, 0.1), 3),
        })
    return pd.DataFrame(records)


def generate_cyclone_track(n_points: int = 20) -> pd.DataFrame:
    """Generate a realistic cyclone track across the Bay of Bengal toward Indian coast."""
    start_lat, start_lon = 8.5, 93.0
    rows = []
    lat, lon = start_lat, start_lon
    wind_speed = 30.0
    pressure = 998.0

    for i in range(n_points):
        hours_from_now = (i - n_points // 2) * 6
        ts = datetime.utcnow() + timedelta(hours=hours_from_now)
        is_past = hours_from_now < 0

        intensity = get_intensity_label(wind_speed)
        rows.append({
            "timestamp":      ts,
            "hours_offset":   hours_from_now,
            "lat":            round(lat, 3),
            "lon":            round(lon, 3),
            "wind_speed_kts": round(wind_speed, 1),
            "pressure_hpa":   round(pressure, 1),
            "intensity":      intensity["label"],
            "color":          intensity["color"],
            "is_forecast":    not is_past,
            "radius_km":      round(150 + wind_speed * 2, 0),
        })

        # Movement: NW direction, accelerating toward coast
        lat     += 0.7 + 0.03 * i + _RNG.normal(0, 0.05)
        lon     -= 0.9 + 0.02 * i + _RNG.normal(0, 0.05)
        wind_speed = min(160, wind_speed + 3.5 + _RNG.normal(0, 1))
        pressure   = max(900, pressure - 2.8 + _RNG.normal(0, 0.5))

    return pd.DataFrame(rows)


def generate_sea_surface_temp_grid() -> pd.DataFrame:
    """Generate an SST grid for the Bay of Bengal."""
    lats = np.arange(5, 23, 1.0)
    lons = np.arange(80, 101, 1.0)
    rows = []
    for lat in lats:
        for lon in lons:
            # Warmer SST near cyclone center (13N, 88E)
            dist = np.sqrt((lat - 13)**2 + (lon - 88)**2)
            sst  = round(30.0 - 0.3 * dist + _RNG.normal(0, 0.2), 2)
            rows.append({"lat": lat, "lon": lon, "sst": sst})
    return pd.DataFrame(rows)


def generate_impact_assessment() -> list[dict]:
    """Generate risk scores for coastal cities."""
    track_df = generate_cyclone_track()
    landfall_row = track_df[track_df["hours_offset"] >= 0].iloc[0] if not track_df.empty else None

    results = []
    for city in COASTAL_CITIES:
        if landfall_row is not None:
            dist_km = np.sqrt(
                ((city["lat"] - float(landfall_row["lat"])) * 111)**2 +
                ((city["lon"] - float(landfall_row["lon"])) * 111 * np.cos(np.radians(city["lat"])))**2
            )
        else:
            dist_km = 500

        wind_risk       = max(0, min(100, round(100 - dist_km * 0.15 + _RNG.normal(0, 3), 1)))
        surge_risk      = max(0, min(100, round(90 - dist_km * 0.12 + _RNG.normal(0, 3), 1)))
        flood_risk      = max(0, min(100, round(85 - dist_km * 0.10 + _RNG.normal(0, 3), 1)))
        overall_risk    = round((wind_risk + surge_risk + flood_risk) / 3, 1)
        risk_level      = (
            "CRITICAL" if overall_risk >= 70 else
            "HIGH"     if overall_risk >= 50 else
            "MODERATE" if overall_risk >= 30 else "LOW"
        )
        results.append({
            "city":        city["name"],
            "state":       city["state"],
            "lat":         city["lat"],
            "lon":         city["lon"],
            "pop_M":       city["pop_M"],
            "dist_km":     round(dist_km, 0),
            "wind_risk":   wind_risk,
            "surge_risk":  surge_risk,
            "flood_risk":  flood_risk,
            "overall_risk": overall_risk,
            "risk_level":  risk_level,
        })
    return sorted(results, key=lambda x: -x["overall_risk"])


def generate_historical_cyclones() -> pd.DataFrame:
    """Representative historical cyclone records for Indian Ocean (2000-2023)."""
    data = [
        {"name":"Amphan",  "year":2020,"peak_ws":155,"peak_cat":"Super Cyclonic","deaths":128,"damage_crore":100000,"landfall":"West Bengal"},
        {"name":"Fani",    "year":2019,"peak_ws":130,"peak_cat":"Extremely Severe","deaths":89, "damage_crore":68000,"landfall":"Odisha"},
        {"name":"Titli",   "year":2018,"peak_ws":90, "peak_cat":"Very Severe","deaths":72, "damage_crore":9000, "landfall":"Andhra Pradesh"},
        {"name":"Ockhi",   "year":2017,"peak_ws":95, "peak_cat":"Very Severe","deaths":245,"damage_crore":4000, "landfall":"Gujarat"},
        {"name":"Vardah",  "year":2016,"peak_ws":75, "peak_cat":"Very Severe","deaths":18, "damage_crore":6000, "landfall":"Tamil Nadu"},
        {"name":"Hudhud",  "year":2014,"peak_ws":105,"peak_cat":"Extremely Severe","deaths":124,"damage_crore":21908,"landfall":"Andhra Pradesh"},
        {"name":"Phailin", "year":2013,"peak_ws":115,"peak_cat":"Extremely Severe","deaths":45, "damage_crore":15000,"landfall":"Odisha"},
        {"name":"Nilam",   "year":2012,"peak_ws":55, "peak_cat":"Severe","deaths":55, "damage_crore":3000, "landfall":"Tamil Nadu"},
        {"name":"Thane",   "year":2011,"peak_ws":85, "peak_cat":"Very Severe","deaths":48, "damage_crore":6000, "landfall":"Tamil Nadu"},
        {"name":"Gonu",    "year":2007,"peak_ws":140,"peak_cat":"Super Cyclonic","deaths":50, "damage_crore":25000,"landfall":"Oman/Gujarat"},
        {"name":"Sidr",    "year":2007,"peak_ws":120,"peak_cat":"Extremely Severe","deaths":10000,"damage_crore":50000,"landfall":"Bangladesh"},
        {"name":"Laila",   "year":2010,"peak_ws":65, "peak_cat":"Severe","deaths":65, "damage_crore":2000, "landfall":"Andhra Pradesh"},
        {"name":"Biparjoy","year":2023,"peak_ws":85, "peak_cat":"Very Severe","deaths":3,  "damage_crore":7500, "landfall":"Gujarat"},
        {"name":"Mocha",   "year":2023,"peak_ws":135,"peak_cat":"Super Cyclonic","deaths":400,"damage_crore":3200,"landfall":"Myanmar"},
        {"name":"Mandous", "year":2022,"peak_ws":65, "peak_cat":"Severe","deaths":8,  "damage_crore":1200, "landfall":"Tamil Nadu"},
        {"name":"Asani",   "year":2022,"peak_ws":80, "peak_cat":"Very Severe","deaths":0,  "damage_crore":500,  "landfall":"Dissipated"},
        {"name":"Yaas",    "year":2021,"peak_ws":90, "peak_cat":"Very Severe","deaths":19, "damage_crore":22000,"landfall":"Odisha"},
        {"name":"Tauktae", "year":2021,"peak_ws":110,"peak_cat":"Extremely Severe","deaths":198,"damage_crore":20000,"landfall":"Gujarat"},
    ]
    return pd.DataFrame(data).sort_values("year", ascending=False).reset_index(drop=True)

# ------------------------------------------------------------------
# COASTAL ZONES — 5 divisions of the Indian coastline
# ------------------------------------------------------------------
COASTAL_ZONES = {
    "🟦 Northeast Coast": {
        "id":          "northeast",
        "label":       "Northeast Coast",
        "emoji":       "🟦",
        "sea":         "Bay of Bengal",
        "states":      ["West Bengal", "Odisha"],
        "color":       "#4FC3F7",
        "lat_min":     18.5,  "lat_max": 23.5,
        "lon_min":     85.0,  "lon_max": 92.0,
        "center_lat":  21.0,  "center_lon": 87.5,
        "zoom":        5.5,
        "risk_profile":"Very High — frequent landfall zone (Amphan, Fani, Yaas)",
        "track_origin": (8.5, 93.0),
        "track_dir":   (0.8, -0.9),
        "cities": [
            {"name":"Kolkata",  "lat":22.57,"lon":88.36,"pop_M":14.8,"district":"South 24 Parganas"},
            {"name":"Paradip",  "lat":20.32,"lon":86.61,"pop_M":0.3, "district":"Jagatsinghpur"},
            {"name":"Puri",     "lat":19.81,"lon":85.83,"pop_M":0.2, "district":"Puri"},
            {"name":"Bhubaneswar","lat":20.29,"lon":85.82,"pop_M":1.0,"district":"Khordha"},
            {"name":"Balasore", "lat":21.49,"lon":86.93,"pop_M":0.2, "district":"Balasore"},
            {"name":"Digha",    "lat":21.62,"lon":87.50,"pop_M":0.1, "district":"Purba Medinipur"},
            {"name":"Gopalpur", "lat":19.27,"lon":84.90,"pop_M":0.05,"district":"Ganjam"},
            {"name":"Chandbali","lat":20.78,"lon":86.74,"pop_M":0.08,"district":"Bhadrak"},
        ],
        "shelters":     720,
        "ndrf_teams":   8,
        "cyclone_freq": "Very High (5–7 per decade)",
        "peak_season":  "Oct–Dec, Apr–May",
        "elevation_risk":"Low-lying delta — high storm surge risk",
        "historical_hits": ["Amphan (2020)","Fani (2019)","Yaas (2021)","Sidr (2007)"],
    },
    "🟧 Southeast Coast": {
        "id":          "southeast",
        "label":       "Southeast Coast",
        "emoji":       "🟧",
        "sea":         "Bay of Bengal",
        "states":      ["Andhra Pradesh", "Tamil Nadu", "Puducherry"],
        "color":       "#FFB74D",
        "lat_min":     8.0,   "lat_max": 18.5,
        "lon_min":     79.0,  "lon_max": 85.0,
        "center_lat":  13.5,  "center_lon": 81.5,
        "zoom":        5.0,
        "risk_profile":"High — faces North Indian Ocean cyclones from Bay of Bengal",
        "track_origin": (9.0, 90.0),
        "track_dir":   (0.5, -1.1),
        "cities": [
            {"name":"Visakhapatnam","lat":17.69,"lon":83.22,"pop_M":2.0,"district":"Visakhapatnam"},
            {"name":"Chennai",      "lat":13.08,"lon":80.27,"pop_M":10.9,"district":"Chennai"},
            {"name":"Kakinada",     "lat":16.94,"lon":82.24,"pop_M":0.35,"district":"East Godavari"},
            {"name":"Machilipatnam","lat":16.18,"lon":81.13,"pop_M":0.18,"district":"Krishna"},
            {"name":"Ongole",       "lat":15.50,"lon":80.05,"pop_M":0.15,"district":"Prakasam"},
            {"name":"Nellore",      "lat":14.44,"lon":79.99,"pop_M":0.5,"district":"Nellore"},
            {"name":"Mahabalipuram","lat":12.62,"lon":80.19,"pop_M":0.04,"district":"Chengalpattu"},
            {"name":"Nagapattinam", "lat":10.76,"lon":79.84,"pop_M":0.12,"district":"Nagapattinam"},
        ],
        "shelters":     610,
        "ndrf_teams":   7,
        "cyclone_freq": "High (4–6 per decade)",
        "peak_season":  "Oct–Dec",
        "elevation_risk":"Moderate — coastal plains with river deltas",
        "historical_hits": ["Hudhud (2014)","Vardah (2016)","Titli (2018)","Nilam (2012)"],
    },
    "🟩 Southwest Coast": {
        "id":          "southwest",
        "label":       "Southwest Coast",
        "emoji":       "🟩",
        "sea":         "Arabian Sea",
        "states":      ["Kerala", "Karnataka"],
        "color":       "#81C784",
        "lat_min":     8.0,   "lat_max": 15.5,
        "lon_min":     74.0,  "lon_max": 78.0,
        "center_lat":  11.5,  "center_lon": 75.5,
        "zoom":        5.5,
        "risk_profile":"Moderate — occasional Arabian Sea cyclones; high landslide & flood risk",
        "track_origin": (9.0, 65.0),
        "track_dir":   (0.4, 1.05),
        "cities": [
            {"name":"Thiruvananthapuram","lat":8.52,"lon":76.94,"pop_M":1.7,"district":"Thiruvananthapuram"},
            {"name":"Kochi",             "lat":9.93,"lon":76.26,"pop_M":2.2,"district":"Ernakulam"},
            {"name":"Kozhikode",         "lat":11.25,"lon":75.78,"pop_M":0.6,"district":"Kozhikode"},
            {"name":"Mangaluru",         "lat":12.91,"lon":74.86,"pop_M":0.6,"district":"Dakshina Kannada"},
            {"name":"Udupi",             "lat":13.34,"lon":74.74,"pop_M":0.17,"district":"Udupi"},
            {"name":"Kannur",            "lat":11.87,"lon":75.37,"pop_M":0.3,"district":"Kannur"},
            {"name":"Kollam",            "lat":8.88,"lon":76.60,"pop_M":0.35,"district":"Kollam"},
            {"name":"Thrissur",          "lat":10.52,"lon":76.21,"pop_M":0.32,"district":"Thrissur"},
        ],
        "shelters":     320,
        "ndrf_teams":   3,
        "cyclone_freq": "Low-Moderate (1–2 per decade)",
        "peak_season":  "May–Jun, Oct–Nov",
        "elevation_risk":"Steep Western Ghats — flash floods & landslides compound risk",
        "historical_hits": ["Ockhi (2017)","Tauktae (2021-skirted)"],
    },
    "🟥 Northwest Coast": {
        "id":          "northwest",
        "label":       "Northwest Coast",
        "emoji":       "🟥",
        "sea":         "Arabian Sea",
        "states":      ["Goa", "Maharashtra", "Gujarat"],
        "color":       "#E84545",
        "lat_min":     14.5,  "lat_max": 24.5,
        "lon_min":     68.0,  "lon_max": 75.0,
        "center_lat":  19.5,  "center_lon": 72.0,
        "zoom":        5.0,
        "risk_profile":"Moderate-High — increasing frequency due to warming Arabian Sea",
        "track_origin": (9.5, 63.0),
        "track_dir":   (0.5, 0.95),
        "cities": [
            {"name":"Mumbai",   "lat":19.08,"lon":72.88,"pop_M":20.7,"district":"Mumbai"},
            {"name":"Surat",    "lat":21.17,"lon":72.83,"pop_M":6.1, "district":"Surat"},
            {"name":"Porbandar","lat":21.64,"lon":69.61,"pop_M":0.3, "district":"Porbandar"},
            {"name":"Veraval",  "lat":20.90,"lon":70.37,"pop_M":0.18,"district":"Junagadh"},
            {"name":"Bhavnagar","lat":21.76,"lon":72.15,"pop_M":0.65,"district":"Bhavnagar"},
            {"name":"Jamnagar", "lat":22.47,"lon":70.06,"pop_M":0.6, "district":"Jamnagar"},
            {"name":"Vapi",     "lat":20.37,"lon":72.90,"pop_M":0.18,"district":"Valsad"},
            {"name":"Panaji",   "lat":15.49,"lon":73.82,"pop_M":0.11,"district":"North Goa"},
        ],
        "shelters":     410,
        "ndrf_teams":   5,
        "cyclone_freq": "Moderate (2–4 per decade, increasing)",
        "peak_season":  "May–Jun",
        "elevation_risk":"Low-lying Gulf of Kutch & Khambhat — surge risk; Mumbai flooding risk",
        "historical_hits": ["Tauktae (2021)","Biparjoy (2023)","Gonu (2007)"],
    },
    "🟪 Island Territories": {
        "id":          "islands",
        "label":       "Island Territories",
        "emoji":       "🟪",
        "sea":         "Bay of Bengal / Arabian Sea",
        "states":      ["Andaman & Nicobar Islands", "Lakshadweep"],
        "color":       "#CE93D8",
        "lat_min":     8.0,   "lat_max": 14.0,
        "lon_min":     72.0,  "lon_max": 94.0,
        "center_lat":  10.5,  "center_lon": 82.5,
        "zoom":        4.0,
        "risk_profile":"Critical — isolated islands, direct cyclone paths, limited evacuation",
        "track_origin": (5.5, 95.0),
        "track_dir":   (0.6, -0.6),
        "cities": [
            {"name":"Port Blair",      "lat":11.62,"lon":92.73,"pop_M":0.11,"district":"South Andaman"},
            {"name":"Car Nicobar",     "lat": 9.15,"lon":92.82,"pop_M":0.03,"district":"Nicobar"},
            {"name":"Kavaratti",       "lat":10.56,"lon":72.64,"pop_M":0.01,"district":"Lakshadweep"},
            {"name":"Havelock Island", "lat":12.06,"lon":92.98,"pop_M":0.01,"district":"South Andaman"},
            {"name":"Campbell Bay",    "lat": 7.00,"lon":93.93,"pop_M":0.01,"district":"Nicobar"},
            {"name":"Diglipur",        "lat":13.27,"lon":92.97,"pop_M":0.04,"district":"North & Middle Andaman"},
        ],
        "shelters":     45,
        "ndrf_teams":   2,
        "cyclone_freq": "Very High — located in cyclone genesis zone",
        "peak_season":  "Year-round",
        "elevation_risk":"Low coral islands — total inundation risk from storm surge",
        "historical_hits": ["Mocha (2023)","Multiple unnamed storms"],
    },
}

ALL_ZONES_KEY = "🌏 All India Coastline"


def get_zone_cities(zone_key: str) -> list[dict]:
    """Return city list for a zone key, or all cities for ALL_ZONES_KEY."""
    if zone_key == ALL_ZONES_KEY:
        cities = []
        for z in COASTAL_ZONES.values():
            for c in z["cities"]:
                cities.append({**c, "zone": z["label"], "color": z["color"]})
        return cities
    z = COASTAL_ZONES.get(zone_key)
    if z:
        return [{**c, "zone": z["label"], "color": z["color"]} for c in z["cities"]]
    return []


def generate_zone_track(zone_key: str, n_points: int = 20) -> pd.DataFrame:
    """Generate a cyclone track customised to a specific coastal zone."""
    if zone_key == ALL_ZONES_KEY:
        return generate_cyclone_track(n_points)

    z = COASTAL_ZONES.get(zone_key)
    if not z:
        return generate_cyclone_track(n_points)

    start_lat, start_lon = z["track_origin"]
    dlat, dlon           = z["track_dir"]
    rows = []
    lat, lon   = start_lat, start_lon
    wind_speed = 30.0
    pressure   = 998.0

    for i in range(n_points):
        hours_from_now = (i - n_points // 2) * 6
        ts      = datetime.utcnow() + timedelta(hours=hours_from_now)
        is_past = hours_from_now < 0
        intensity = get_intensity_label(wind_speed)
        rows.append({
            "timestamp":      ts,
            "hours_offset":   hours_from_now,
            "lat":            round(lat, 3),
            "lon":            round(lon, 3),
            "wind_speed_kts": round(wind_speed, 1),
            "pressure_hpa":   round(pressure, 1),
            "intensity":      intensity["label"],
            "color":          intensity["color"],
            "is_forecast":    not is_past,
            "radius_km":      round(150 + wind_speed * 2, 0),
            "zone":           z["label"],
        })
        lat        += dlat + 0.03 * i + _RNG.normal(0, 0.05)
        lon        += dlon + 0.02 * i * (1 if dlon > 0 else -1) + _RNG.normal(0, 0.05)
        wind_speed  = min(160, wind_speed + 3.5 + _RNG.normal(0, 1))
        pressure    = max(900, pressure - 2.8 + _RNG.normal(0, 0.5))

    return pd.DataFrame(rows)


def generate_zone_impact(zone_key: str) -> list[dict]:
    """Generate impact assessment scoped to a coastal zone."""
    if zone_key == ALL_ZONES_KEY:
        return generate_impact_assessment()

    z = COASTAL_ZONES.get(zone_key)
    if not z:
        return generate_impact_assessment()

    track_df = generate_zone_track(zone_key)
    landfall_row = track_df[track_df["hours_offset"] >= 0].iloc[0] if not track_df.empty else None

    results = []
    for city in z["cities"]:
        if landfall_row is not None:
            dist_km = np.sqrt(
                ((city["lat"] - float(landfall_row["lat"])) * 111)**2 +
                ((city["lon"] - float(landfall_row["lon"])) * 111 * np.cos(np.radians(city["lat"])))**2
            )
        else:
            dist_km = 300

        wind_risk    = max(0, min(100, round(100 - dist_km * 0.18 + _RNG.normal(0, 3), 1)))
        surge_risk   = max(0, min(100, round(90  - dist_km * 0.14 + _RNG.normal(0, 3), 1)))
        flood_risk   = max(0, min(100, round(85  - dist_km * 0.11 + _RNG.normal(0, 3), 1)))
        overall_risk = round((wind_risk + surge_risk + flood_risk) / 3, 1)
        risk_level   = (
            "CRITICAL" if overall_risk >= 70 else
            "HIGH"     if overall_risk >= 50 else
            "MODERATE" if overall_risk >= 30 else "LOW"
        )
        results.append({
            "city":         city["name"],
            "state":        z["states"][0],
            "district":     city.get("district", ""),
            "zone":         z["label"],
            "lat":          city["lat"],
            "lon":          city["lon"],
            "pop_M":        city.get("pop_M", 0.1),
            "dist_km":      round(dist_km, 0),
            "wind_risk":    wind_risk,
            "surge_risk":   surge_risk,
            "flood_risk":   flood_risk,
            "overall_risk": overall_risk,
            "risk_level":   risk_level,
        })
    return sorted(results, key=lambda x: -x["overall_risk"])

