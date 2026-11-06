import sys, warnings
warnings.filterwarnings('ignore')
sys.path.insert(0, 'd:\\CycloneDetectionEarlyWarning')

from utils.data_generator import (
    COASTAL_ZONES, ALL_ZONES_KEY,
    get_zone_cities, generate_zone_track, generate_zone_impact,
)

print('=== Testing Coastal Zone Data ===')
print('Zones defined:', len(COASTAL_ZONES))
for k, z in COASTAL_ZONES.items():
    cities = get_zone_cities(k)
    track  = generate_zone_track(k, n_points=10)
    impact = generate_zone_impact(k)
    print(f'  {z["emoji"]} {z["label"]}: {len(cities)} cities, track={len(track)} pts, impact={len(impact)} assessments')

all_cities = get_zone_cities(ALL_ZONES_KEY)
print(f'All India: {len(all_cities)} total cities')

print()
print('=== Testing Zone Track ===')
for zone_key in list(COASTAL_ZONES.keys())[:2]:
    t = generate_zone_track(zone_key)
    cur = t.loc[t["hours_offset"].abs().idxmin()]
    print(f'  {COASTAL_ZONES[zone_key]["label"]}: current={cur["intensity"]} at {cur["lat"]}N,{cur["lon"]}E')

print()
print('ALL ZONE TESTS PASSED')
