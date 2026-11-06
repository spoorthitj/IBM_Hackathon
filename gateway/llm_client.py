"""
Gateway — Unified Multi-LLM Client
Supports: IBM watsonx.ai · Google Gemini · Groq · Replicate · OpenRouter
Per-agent LLM routing via llm_router registry.
Records every call to analytics/metrics_tracker.
"""
import os, time, warnings
from dotenv import load_dotenv

load_dotenv()

# ── Credentials ──────────────────────────────────────────────────
WATSONX_API_KEY    = os.getenv("WATSONX_API_KEY", "")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
WATSONX_URL        = os.getenv("WATSONX_URL", "https://eu-gb.ml.cloud.ibm.com")

GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL_ID    = os.getenv("GEMINI_MODEL_ID", "gemini-1.5-pro")

GROQ_API_KEY       = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL_ID      = os.getenv("GROQ_MODEL_ID", "llama3-70b-8192")

REPLICATE_API_KEY  = os.getenv("REPLICATE_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL   = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")

# ── Cached clients ────────────────────────────────────────────────
_clients: dict = {}
_active_provider: str | None = None

_WATSONX_FALLBACK_MODELS = [
    "ibm/granite-13b-instruct-v2",
    "ibm/granite-3-8b-instruct",
    "ibm/granite-3-3-8b-instruct",
    "meta-llama/llama-3-3-70b-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct-fp8",
    "mistralai/mistral-small-3-1-24b-instruct-2503",
]

PROVIDER_COLORS = {
    "watsonx": "#4FC3F7", "gemini": "#81C784",
    "groq": "#FFB74D", "replicate": "#CE93D8",
    "openrouter": "#A5D6A7", "demo": "#8B949E",
}

# Cost per 1K tokens (USD) — used by comparator and metrics
_COST_MAP: dict[str, float] = {
    "watsonx":    0.0006,
    "gemini":     0.0010,
    "groq":       0.0004,
    "replicate":  0.0008,
    "openrouter": 0.0003,
    "demo":       0.0,
}


# ── Initialisers ──────────────────────────────────────────────────

def _init_watsonx() -> tuple[bool, str]:
    if not WATSONX_API_KEY or "your_ibm" in WATSONX_API_KEY:
        return False, ""
    try:
        from ibm_watsonx_ai import APIClient, Credentials
        from ibm_watsonx_ai.foundation_models import ModelInference
        from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GP
        creds = Credentials(url=WATSONX_URL, api_key=WATSONX_API_KEY)
        resolved = None
        for mid in _WATSONX_FALLBACK_MODELS:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    ModelInference(model_id=mid, credentials=creds,
                                   project_id=WATSONX_PROJECT_ID, params={GP.MAX_NEW_TOKENS: 1})
                resolved = mid; break
            except Exception:
                continue
        if not resolved:
            return False, ""
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _clients["watsonx"] = ModelInference(
                model_id=resolved, credentials=creds, project_id=WATSONX_PROJECT_ID,
                params={GP.DECODING_METHOD:"greedy", GP.MAX_NEW_TOKENS:1000,
                        GP.MIN_NEW_TOKENS:30, GP.TEMPERATURE:0.3, GP.REPETITION_PENALTY:1.1})
        return True, resolved
    except Exception as e:
        print(f"[gateway] watsonx failed: {e}")
        return False, ""


def _init_gemini() -> bool:
    if not GEMINI_API_KEY or "your_gemini" in GEMINI_API_KEY:
        return False
    try:
        import google.genai as genai
        client = genai.Client(api_key=GEMINI_API_KEY)
        client.models.generate_content(model=GEMINI_MODEL_ID, contents="ping")
        _clients["gemini"] = client
        return True
    except Exception:
        return False


def _init_groq() -> bool:
    if not GROQ_API_KEY or "your_groq" in GROQ_API_KEY:
        return False
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        client.chat.completions.create(model=GROQ_MODEL_ID,
            messages=[{"role":"user","content":"ping"}], max_tokens=1)
        _clients["groq"] = client
        return True
    except Exception:
        return False


def _init_openrouter() -> bool:
    if not OPENROUTER_API_KEY or "your_openrouter" in OPENROUTER_API_KEY:
        return False
    try:
        from openai import OpenAI
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)
        client.chat.completions.create(model=OPENROUTER_MODEL,
            messages=[{"role":"user","content":"ping"}], max_tokens=1)
        _clients["openrouter"] = client
        return True
    except Exception:
        return False


def init_all():
    """Initialise all configured providers."""
    global _active_provider
    if _active_provider:
        return
    ok, model = _init_watsonx()
    if ok:
        _active_provider = "watsonx"
        print(f"[gateway] Primary: watsonx — {model}")
    if _init_gemini():
        print("[gateway] Gemini ready")
    if _init_groq():
        print("[gateway] Groq ready")
    if _init_openrouter():
        print("[gateway] OpenRouter ready")
    if not _active_provider:
        _active_provider = "demo"
        print("[gateway] All providers unavailable — demo mode")


# ── Core generation ────────────────────────────────────────────────

def generate_with(provider: str, prompt: str, agent_name: str = "") -> str:
    """Generate using a specific provider. Falls back to demo."""
    init_all()
    try:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        in_tok = len(enc.encode(prompt))
    except Exception:
        in_tok = int(len(prompt.split()) * 1.3)

    t0 = time.time()
    text, err = "", None

    try:
        if provider == "watsonx" and "watsonx" in _clients:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                text = _clients["watsonx"].generate_text(prompt=prompt)

        elif provider == "gemini" and "gemini" in _clients:
            resp = _clients["gemini"].models.generate_content(
                model=GEMINI_MODEL_ID, contents=prompt)
            text = resp.text or ""

        elif provider == "groq" and "groq" in _clients:
            resp = _clients["groq"].chat.completions.create(
                model=GROQ_MODEL_ID,
                messages=[{"role":"user","content":prompt}],
                max_tokens=1000, temperature=0.3)
            text = resp.choices[0].message.content or ""

        elif provider == "openrouter" and "openrouter" in _clients:
            resp = _clients["openrouter"].chat.completions.create(
                model=OPENROUTER_MODEL,
                messages=[{"role":"user","content":prompt}],
                max_tokens=1000)
            text = resp.choices[0].message.content or ""

        elif provider == "replicate":
            import replicate as rep
            os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_KEY
            out = rep.run("meta/llama-2-70b-chat:02e509c789964a7ea8736978a43525956ef40397be9033abf9fd2badfe68c9e3",
                          input={"prompt": prompt, "max_new_tokens": 800})
            text = "".join(out)

        else:
            # fallback chain
            for fb in ["watsonx","gemini","groq","openrouter"]:
                if fb in _clients:
                    return generate_with(fb, prompt, agent_name)
            text = _demo_response(prompt)

    except Exception as e:
        err = str(e)
        text = _demo_response(prompt)

    lat = round((time.time() - t0) * 1000, 1)
    try:
        out_tok = len(tiktoken.get_encoding("cl100k_base").encode(text))
    except Exception:
        out_tok = len(text.split())

    _record(provider, agent_name, in_tok, out_tok, lat, err is None, err)
    return text


def generate(prompt: str, agent_name: str = "") -> str:
    """Generate using the primary active provider."""
    init_all()
    return generate_with(_active_provider or "demo", prompt, agent_name)


def get_active_provider() -> str:
    init_all(); return _active_provider or "demo"


def get_active_model() -> str:
    p = get_active_provider()
    if p == "watsonx" and "watsonx" in _clients:
        return _clients["watsonx"].model_id
    if p == "gemini":  return GEMINI_MODEL_ID
    if p == "groq":    return GROQ_MODEL_ID
    if p == "openrouter": return OPENROUTER_MODEL
    return "demo"


def available_providers() -> list[str]:
    init_all()
    return list(_clients.keys()) or ["demo"]


def is_demo_mode() -> bool:
    return get_active_provider() == "demo"


def _record(provider, agent, in_tok, out_tok, lat, ok, err):
    try:
        from analytics.metrics_tracker import record_llm_call
        record_llm_call(provider=provider, model=get_active_model(),
                        agent_name=agent, input_tokens=in_tok,
                        output_tokens=out_tok, latency_ms=lat, success=ok, error=err)
    except Exception:
        pass


def _demo_response(prompt: str) -> str:
    pl = prompt.lower()
    if "weather" in pl or "meteorol" in pl:
        return ("**Weather Analysis (Demo)**\n\nSST 29.8°C, pressure 987 hPa dropping rapidly. "
                "Wind shear 8 m/s. Conditions highly conducive to cyclogenesis.")
    if "detect" in pl:
        return ("**Cyclone Detection (Demo)**\n\n🔴 Cyclonic vortex confirmed at 10.2°N, 87.6°E. "
                "Dvorak T3.0. Spiral score 0.78. Classification: Deep Depression → Cyclonic Storm.")
    if "track" in pl or "trajectory" in pl:
        return ("**Track Advisory (Demo)**\n\nSystem tracking NNW at 14 km/h. "
                "Landfall expected near Visakhapatnam in +48h. Confidence: HIGH for 24h.")
    if "intensity" in pl:
        return ("**Intensity Forecast (Demo)**\n\nRI probability 68%. Peak 120–130 kts in 36h. "
                "Landfall intensity: 90–110 kts (Extremely Severe).")
    if "impact" in pl:
        return ("**Impact Assessment (Demo)**\n\nHigh risk: Visakhapatnam, Srikakulam (4.2M at risk). "
                "Storm surge 3–5m. 2.1 lakh hectares of crops at risk.")
    if "warn" in pl or "alert" in pl:
        return ("**Early Warning (Demo)**\n\n🔴 RED ALERT — Andhra Pradesh & Odisha coast. "
                "Immediate evacuation of 10 km coastal strip advised.")
    return ("**Disaster Response (Demo)**\n\nActivate EOC. Deploy 12 NDRF teams. "
            "385 shelters active — 8.2 lakh capacity. Evacuate 3.85 lakh persons.")
