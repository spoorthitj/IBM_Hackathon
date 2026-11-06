"""
Multi-LLM Client — supports IBM watsonx.ai, Google Gemini, Groq (LLaMA 3), Replicate.
Tries providers in priority order; falls back gracefully to demo mode.
Records per-call metrics for the evaluation dashboard.
"""
import os, time, warnings
from dotenv import load_dotenv
from utils.metrics_tracker import record_llm_call

load_dotenv()

# ── Credentials ─────────────────────────────────────────────────
WATSONX_API_KEY    = os.getenv("WATSONX_API_KEY", "")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID", "")
WATSONX_URL        = os.getenv("WATSONX_URL", "https://eu-gb.ml.cloud.ibm.com")
WATSONX_MODEL_ID   = os.getenv("WATSONX_MODEL_ID", "ibm/granite-13b-instruct-v2")

GEMINI_API_KEY     = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL_ID    = os.getenv("GEMINI_MODEL_ID", "gemini-1.5-pro")

GROQ_API_KEY       = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL_ID      = os.getenv("GROQ_MODEL_ID", "llama3-70b-8192")

REPLICATE_API_KEY  = os.getenv("REPLICATE_API_KEY", "")

# ── Cached clients ───────────────────────────────────────────────
_watsonx_model = None
_gemini_client = None
_groq_client   = None
_active_provider = None   # "watsonx" | "gemini" | "groq" | "replicate" | "demo"

_WATSONX_FALLBACK_MODELS = [
    "ibm/granite-13b-instruct-v2",
    "ibm/granite-3-8b-instruct",
    "ibm/granite-3-3-8b-instruct",
    "meta-llama/llama-3-3-70b-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct-fp8",
    "mistralai/mistral-small-3-1-24b-instruct-2503",
]


# ── Provider initialisers ────────────────────────────────────────

def _init_watsonx():
    global _watsonx_model
    if not WATSONX_API_KEY or "your_ibm" in WATSONX_API_KEY:
        return False
    try:
        from ibm_watsonx_ai import APIClient, Credentials
        from ibm_watsonx_ai.foundation_models import ModelInference
        from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GP

        creds = Credentials(url=WATSONX_URL, api_key=WATSONX_API_KEY)
        # probe for working model
        resolved = None
        for mid in _WATSONX_FALLBACK_MODELS:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    m = ModelInference(model_id=mid, credentials=creds,
                                       project_id=WATSONX_PROJECT_ID,
                                       params={GP.MAX_NEW_TOKENS: 1})
                resolved = mid
                break
            except Exception:
                continue
        if not resolved:
            return False
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _watsonx_model = ModelInference(
                model_id=resolved, credentials=creds,
                project_id=WATSONX_PROJECT_ID,
                params={GP.DECODING_METHOD:"greedy", GP.MAX_NEW_TOKENS:800,
                        GP.MIN_NEW_TOKENS:30, GP.TEMPERATURE:0.3,
                        GP.REPETITION_PENALTY:1.1})
        print(f"[LLM] watsonx connected — {resolved}")
        return True
    except Exception as e:
        print(f"[LLM] watsonx failed: {e}")
        return False


def _init_gemini():
    global _gemini_client
    if not GEMINI_API_KEY or "your_gemini" in GEMINI_API_KEY:
        return False
    try:
        import google.genai as genai
        _gemini_client = genai.Client(api_key=GEMINI_API_KEY)
        # quick probe
        _gemini_client.models.generate_content(
            model=GEMINI_MODEL_ID,
            contents="ping"
        )
        print(f"[LLM] Gemini connected — {GEMINI_MODEL_ID}")
        return True
    except Exception as e:
        print(f"[LLM] Gemini failed: {e}")
        return False


def _init_groq():
    global _groq_client
    if not GROQ_API_KEY or "your_groq" in GROQ_API_KEY:
        return False
    try:
        from groq import Groq
        _groq_client = Groq(api_key=GROQ_API_KEY)
        _groq_client.chat.completions.create(
            model=GROQ_MODEL_ID,
            messages=[{"role":"user","content":"ping"}],
            max_tokens=1
        )
        print(f"[LLM] Groq connected — {GROQ_MODEL_ID}")
        return True
    except Exception as e:
        print(f"[LLM] Groq failed: {e}")
        return False


def _auto_init():
    global _active_provider
    if _active_provider:
        return
    if _init_watsonx():
        _active_provider = "watsonx"
    elif _init_gemini():
        _active_provider = "gemini"
    elif _init_groq():
        _active_provider = "groq"
    else:
        _active_provider = "demo"
        print("[LLM] All providers unavailable — demo mode active.")


# ── Public API ───────────────────────────────────────────────────

def get_active_provider() -> str:
    _auto_init()
    return _active_provider or "demo"


def get_active_model() -> str:
    p = get_active_provider()
    if p == "watsonx" and _watsonx_model:
        return _watsonx_model.model_id
    if p == "gemini":
        return GEMINI_MODEL_ID
    if p == "groq":
        return GROQ_MODEL_ID
    if p == "replicate":
        return "replicate/llama-3"
    return "demo"


def generate(prompt: str, agent_name: str = "unknown") -> str:
    """
    Generate text using the best available LLM.
    Records call metrics automatically.
    """
    _auto_init()
    import tiktoken
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        input_tokens = len(enc.encode(prompt))
    except Exception:
        input_tokens = len(prompt.split()) * 1.3

    start = time.time()
    text, error = "", None

    try:
        if _active_provider == "watsonx" and _watsonx_model:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                text = _watsonx_model.generate_text(prompt=prompt)

        elif _active_provider == "gemini" and _gemini_client:
            resp = _gemini_client.models.generate_content(
                model=GEMINI_MODEL_ID, contents=prompt)
            text = resp.text

        elif _active_provider == "groq" and _groq_client:
            resp = _groq_client.chat.completions.create(
                model=GROQ_MODEL_ID,
                messages=[{"role":"user","content":prompt}],
                max_tokens=800, temperature=0.3)
            text = resp.choices[0].message.content

        elif _active_provider == "replicate":
            import replicate as rep
            os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_KEY
            output = rep.run(
                "meta/llama-2-70b-chat:02e509c789964a7ea8736978a43525956ef40397be9033abf9fd2badfe68c9e3",
                input={"prompt": prompt, "max_new_tokens": 800})
            text = "".join(output)

        else:
            text = _demo_response(prompt)

    except Exception as e:
        error = str(e)
        text  = _demo_response(prompt)

    latency_ms = round((time.time() - start) * 1000, 1)
    try:
        enc = tiktoken.get_encoding("cl100k_base")
        output_tokens = len(enc.encode(text))
    except Exception:
        output_tokens = len(text.split())

    record_llm_call(
        provider=_active_provider or "demo",
        model=get_active_model(),
        agent_name=agent_name,
        input_tokens=int(input_tokens),
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        success=error is None,
        error=error,
    )
    return text


def is_demo_mode() -> bool:
    return get_active_provider() == "demo"


# ── Demo fallback (mirrors watsonx_client.py) ───────────────────
from utils.watsonx_client import _demo_response  # reuse existing demo responses
