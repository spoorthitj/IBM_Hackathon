"""
Memory — Knowledge Base
Seeds the vector store with cyclone domain facts on first use.
"""
from memory.vector_store import store_document, collection_count

DOMAIN_FACTS = [
    ("cyclone_formation_conditions",
     "Tropical cyclones form over warm ocean water (SST ≥ 26°C), with high humidity, "
     "low vertical wind shear (< 10 m/s), and a pre-existing atmospheric disturbance. "
     "The Coriolis effect is needed — cyclones cannot form within 5° of the equator."),
    ("imd_intensity_scale",
     "IMD Cyclone Intensity Scale: Depression (17-27 kts), Deep Depression (28-33), "
     "Cyclonic Storm (34-47), Severe (48-63), Very Severe (64-89), "
     "Extremely Severe (90-119), Super Cyclonic Storm (≥120 kts)."),
    ("rapid_intensification",
     "Rapid Intensification (RI) defined as ≥35 knot increase in 24 hours. "
     "Occurs with SST > 29°C, low shear, high ocean heat content, moist mid-troposphere. "
     "RI is the most dangerous aspect of modern cyclone forecasting."),
    ("bay_of_bengal_risk",
     "Bay of Bengal accounts for ~7% of global tropical cyclones but causes "
     "disproportionate damage. Shallow bathymetry amplifies storm surges. "
     "Northeast India coast (Odisha, West Bengal) is the most vulnerable globally."),
    ("arabian_sea_trend",
     "Arabian Sea cyclone frequency has increased 52% since 1998 due to warming SSTs. "
     "Pre-monsoon (April-June) season now produces intense cyclones affecting Gujarat and Maharashtra."),
    ("storm_surge",
     "Storm surge is the abnormal rise of seawater driven by cyclone winds. "
     "Can reach 3-5m in flat coastal areas. Combined with high tide (storm tide) "
     "can inundate areas 10-15 km inland. Primary cause of cyclone deaths."),
    ("ndma_response_protocol",
     "NDMA cyclone response: Pre-cyclone (72h): warning issue. "
     "48h: NDRF teams deployed. 24h: evacuation begins. "
     "6h: shelter-in-place for remaining. Post: SAR, relief distribution."),
    ("imd_warning_zones",
     "IMD colour warnings: Red (action required, 0-24h), Orange (be prepared, 24-48h), "
     "Yellow (be updated, 48-72h), Green (no warning). "
     "Cyclone warnings issued at T-72h, T-48h, T-24h, T-12h, T-6h intervals."),
]


def seed_knowledge_base():
    """Seed the vector store with domain facts if empty."""
    if collection_count() > 0:
        return
    for doc_id, text in DOMAIN_FACTS:
        store_document(doc_id, text, {"type": "domain_fact", "source": "IMD/NDMA"})
    print(f"[knowledge_base] Seeded {len(DOMAIN_FACTS)} domain facts")
