"""
IBM watsonx.ai Granite LLM client wrapper.
Handles both authenticated (live) and demo (offline) modes gracefully.
"""
import os
import warnings
from dotenv import load_dotenv

load_dotenv()

_client = None
_model  = None
DEMO_MODE = False

WATSONX_URL        = os.getenv("WATSONX_URL", "https://eu-gb.ml.cloud.ibm.com")
WATSONX_API_KEY    = os.getenv("WATSONX_API_KEY", "")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")

# Preferred model order — first available in the environment will be used
_PREFERRED_MODELS = [
    "ibm/granite-3-8b-instruct",
    "ibm/granite-13b-instruct-v2",
    "ibm/granite-3-3-8b-instruct",
    "meta-llama/llama-3-3-70b-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct-fp8",
    "mistralai/mistral-small-3-1-24b-instruct-2503",
]

ACTIVE_MODEL_ID = None


def _resolve_model(client) -> str:
    """
    Probe each preferred model by attempting a minimal ModelInference init.
    Returns the first one that succeeds.
    """
    from ibm_watsonx_ai import Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference
    from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GP

    creds = Credentials(url=WATSONX_URL, api_key=WATSONX_API_KEY)
    for model_id in _PREFERRED_MODELS:
        try:
            ModelInference(
                model_id=model_id,
                credentials=creds,
                project_id=WATSONX_PROJECT_ID,
                params={GP.MAX_NEW_TOKENS: 1},
            )
            return model_id
        except Exception:
            continue
    return _PREFERRED_MODELS[0]


def _init_client():
    global _client, _model, DEMO_MODE, ACTIVE_MODEL_ID
    if not WATSONX_API_KEY or WATSONX_API_KEY == "your_ibm_api_key_here":
        DEMO_MODE = True
        return
    try:
        from ibm_watsonx_ai import APIClient, Credentials
        from ibm_watsonx_ai.foundation_models import ModelInference
        from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GP

        creds   = Credentials(url=WATSONX_URL, api_key=WATSONX_API_KEY)
        _client = APIClient(creds)

        ACTIVE_MODEL_ID = _resolve_model(_client)
        print(f"[watsonx] Connected — model: {ACTIVE_MODEL_ID}")

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _model = ModelInference(
                model_id=ACTIVE_MODEL_ID,
                credentials=creds,
                project_id=WATSONX_PROJECT_ID,
                params={
                    GP.DECODING_METHOD: "greedy",
                    GP.MAX_NEW_TOKENS:  800,
                    GP.MIN_NEW_TOKENS:  50,
                    GP.TEMPERATURE:     0.3,
                    GP.REPETITION_PENALTY: 1.1,
                }
            )
        DEMO_MODE = False
    except Exception as e:
        print(f"[watsonx] Could not connect: {e} — switching to demo mode.")
        DEMO_MODE = True


def generate_text(prompt: str) -> str:
    """Generate text via Granite LLM. Falls back to demo output if offline."""
    global _model
    if _model is None and not DEMO_MODE:
        _init_client()

    if DEMO_MODE or _model is None:
        return _demo_response(prompt)

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result = _model.generate_text(prompt=prompt)
        return result
    except Exception as e:
        return f"[LLM Error] {e}\n\n{_demo_response(prompt)}"


def is_demo_mode() -> bool:
    if _model is None and not DEMO_MODE:
        _init_client()
    return DEMO_MODE


# ------------------------------------------------------------------
# Demo responses keyed by agent type (for offline / showcase mode)
# ------------------------------------------------------------------
_DEMO_RESPONSES = {
    "weather": (
        "**Weather Analysis Summary (Demo Mode)**\n\n"
        "Current meteorological data indicates a significant low-pressure system developing over the "
        "Bay of Bengal at approximately 10°N, 88°E. Sea Surface Temperatures (SST) are anomalously warm "
        "at 29.8°C — 1.3°C above the seasonal average — providing substantial energy for cyclogenesis. "
        "Atmospheric pressure has dropped to 987 hPa over the past 12 hours, a rate of decline consistent "
        "with rapid intensification precursors. Relative humidity in the mid-troposphere is 84%, supporting "
        "deep convection. Wind shear is low at 8 m/s, creating favorable conditions for organised circulation."
    ),
    "detection": (
        "**Cyclone Detection Report (Demo Mode)**\n\n"
        "🔴 **ALERT: Cyclonic circulation detected.**\n\n"
        "Satellite imagery analysis confirms a well-organised Low Pressure Area (LPA) with a Cyclonic "
        "Vortex at 10.2°N, 87.6°E. Cloud band curvature shows anti-clockwise rotation consistent with "
        "Northern Hemisphere cyclonic development. The system has a clearly defined circulation centre "
        "and is intensifying. Dvorak technique analysis assigns a current intensity of T2.5 (35 kts). "
        "Convective bands extending 400 km from centre. **Classification: Deep Depression, likely to "
        "intensify into Cyclonic Storm within 12 hours.**"
    ),
    "tracking": (
        "**Cyclone Track Forecast (Demo Mode)**\n\n"
        "Based on NWP ensemble models and historical analogue systems, the system is forecast to:\n\n"
        "- **+6h**: Intensify to Cyclonic Storm, track NNW at 12 km/h — position 11.1°N, 86.9°E\n"
        "- **+12h**: Severe Cyclonic Storm, track NW at 14 km/h — position 12.5°N, 85.8°E\n"
        "- **+24h**: Very Severe Cyclonic Storm, track NW at 16 km/h — position 15.2°N, 83.5°E\n"
        "- **+48h**: Extremely Severe, approaching Andhra Pradesh/Odisha coast — position 18.8°N, 84.1°E\n"
        "- **+60h**: Landfall near Visakhapatnam–Puri coastal stretch with peak winds 150 km/h\n\n"
        "**Uncertainty cone widens significantly beyond +48h.** Track confidence: HIGH for 24h, MODERATE for 48h."
    ),
    "intensity": (
        "**Intensity Prediction Report (Demo Mode)**\n\n"
        "Current intensity: **55 knots (Severe Cyclonic Storm)**. Forecast peak: **120–130 knots (Extremely Severe).**\n\n"
        "**Rapid Intensification (RI) Alert**: The probability of RI (≥35 kt increase in 24h) is estimated at **68%**. "
        "Key drivers: SST ≥28°C along projected path, low vertical wind shear, moist mid-troposphere, and "
        "favorable upper-level divergence. The system is expected to peak approximately 24–30h before landfall. "
        "Weakening is anticipated as it approaches the coast due to land interaction and increasing shear. "
        "**Landfall intensity estimate: 90–110 knots (Very Severe to Extremely Severe).**"
    ),
    "impact": (
        "**Impact Assessment Report (Demo Mode)**\n\n"
        "**High-Risk Zone (0–150 km from track):** Visakhapatnam, Srikakulam, Vizianagaram districts. "
        "Estimated population at risk: **4.2 million.** Expected storm surge: **3–5 metres** in low-lying coastal areas. "
        "Inundation depth up to 2m likely in Srikakulam and Visakhapatnam port areas.\n\n"
        "**Moderate-Risk Zone (150–300 km):** Puri, Ganjam, East Godavari, Krishna districts. "
        "Estimated population: **8.6 million.**\n\n"
        "**Infrastructure Risk:** HPCL Visakhapatnam Refinery, Gangavaram Port, and NH-16 coastal stretch are "
        "in the direct impact zone. Power disruption expected for 2–7 days post-landfall across 6 districts.\n\n"
        "**Agriculture:** Kharif crops in approximately **2.1 lakh hectares** are at risk of total crop failure."
    ),
    "warning": (
        "**Early Warning Bulletin (Demo Mode)**\n\n"
        "🔴 **RED ALERT — Extremely Severe Cyclonic Storm approaching**\n\n"
        "**Issued by:** Cyclone Detection & Early Warning System | **Valid until:** +72h\n\n"
        "Coastal districts of Andhra Pradesh (Srikakulam, Visakhapatnam, Vizianagaram) and Odisha "
        "(Ganjam, Puri, Khordha) are under RED alert. Fishermen are **strictly advised NOT to venture** "
        "into sea. Evacuation of low-lying coastal areas within 10 km of coast is **strongly recommended.** "
        "Schools, colleges, and non-essential offices to remain closed. Emergency shelters activated at "
        "385 locations. NDRF teams pre-positioned at Visakhapatnam, Bhubaneswar, and Rajahmundry."
    ),
    "response": (
        "**Disaster Response Recommendations (Demo Mode)**\n\n"
        "**Immediate Actions (0–24h):**\n"
        "1. Activate State EOC and alert NDRF/SDRF units in Visakhapatnam and Bhubaneswar\n"
        "2. Evacuate 3,85,000 people from high-risk coastal hamlets to identified cyclone shelters\n"
        "3. Pre-position 5,000 MT relief material (food, water, medicines) at Visakhapatnam and Bhubaneswar\n"
        "4. Deploy Coast Guard and Navy assets for SAR readiness\n\n"
        "**Shelter Capacity:** 385 shelters with combined capacity of 8.2 lakh persons activated in AP and Odisha\n\n"
        "**Post-Landfall (24–72h):** Deploy 12 NDRF teams for search & rescue. Ensure uninterrupted power "
        "restoration teams and medical emergency response. Prioritise restoration of NH-16 and railway connectivity."
    ),
}


def _demo_response(prompt: str) -> str:
    prompt_lower = prompt.lower()
    if "weather" in prompt_lower or "meteorol" in prompt_lower:
        return _DEMO_RESPONSES["weather"]
    if "detect" in prompt_lower:
        return _DEMO_RESPONSES["detection"]
    if "track" in prompt_lower or "trajectory" in prompt_lower or "movement" in prompt_lower:
        return _DEMO_RESPONSES["tracking"]
    if "intensity" in prompt_lower or "rapid" in prompt_lower:
        return _DEMO_RESPONSES["intensity"]
    if "impact" in prompt_lower or "risk" in prompt_lower:
        return _DEMO_RESPONSES["impact"]
    if "warn" in prompt_lower or "alert" in prompt_lower:
        return _DEMO_RESPONSES["warning"]
    if "response" in prompt_lower or "evacuat" in prompt_lower or "disaster" in prompt_lower:
        return _DEMO_RESPONSES["response"]
    return _DEMO_RESPONSES["weather"]
