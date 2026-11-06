"""
Analytics — LLM Comparator
Sends the same prompt to all available providers and scores responses.
"""
import time
from gateway.llm_client import generate_with, available_providers, _COST_MAP, GEMINI_MODEL_ID, GROQ_MODEL_ID

COMPARISON_PROMPT = """You are an expert meteorologist. In exactly 3 bullet points, summarize:
1. The key threat posed by a cyclone with 95 knot winds approaching the Indian coast
2. The most critical action for disaster management authorities in the next 24 hours
3. The primary difference between storm surge and flooding damage

Be concise, factual, and specific."""


def run_comparison(custom_prompt: str | None = None) -> list[dict]:
    """Run the same prompt on all available providers. Returns comparison results."""
    prompt = custom_prompt or COMPARISON_PROMPT
    avail  = available_providers()
    results = []

    for provider in avail:
        if provider == "demo":
            continue
        t0   = time.time()
        text = generate_with(provider, prompt, agent_name="LLM Comparator")
        lat  = round((time.time() - t0) * 1000, 1)

        try:
            import tiktoken
            enc  = tiktoken.get_encoding("cl100k_base")
            itok = len(enc.encode(prompt))
            otok = len(enc.encode(text))
        except Exception:
            itok = int(len(prompt.split()) * 1.3)
            otok = len(text.split())

        rate = _COST_MAP.get(provider, 0.001)
        cost = round((itok + otok) / 1000 * rate, 6)

        results.append({
            "provider":       provider,
            "model":          _get_model_id(provider),
            "response":       text,
            "latency_ms":     lat,
            "input_tokens":   itok,
            "output_tokens":  otok,
            "total_tokens":   itok + otok,
            "cost_usd":       cost,
            "accuracy_score": _score_response(text),
            "word_count":     len(text.split()),
        })

    if not results:
        # demo fallback
        results.append({
            "provider": "demo", "model": "Demo", "latency_ms": 120,
            "input_tokens": 80, "output_tokens": 150, "total_tokens": 230,
            "cost_usd": 0.0, "accuracy_score": 0.75, "word_count": 150,
            "response": "Demo response: Cyclone with 95 kts poses extreme wind and storm surge risk...",
        })
    return results


def _score_response(text: str) -> float:
    """Heuristic accuracy score 0–1 based on keyword coverage."""
    keywords = ["wind","surge","evacuat","pressure","knot","coast",
                "alert","warning","ndma","landfall","flood","damage"]
    hits = sum(1 for kw in keywords if kw in text.lower())
    length_score = min(1.0, len(text.split()) / 150)
    kw_score     = hits / len(keywords)
    return round((kw_score * 0.7 + length_score * 0.3), 3)


def _get_model_id(provider: str) -> str:
    from gateway.llm_client import _clients, OPENROUTER_MODEL
    if provider == "watsonx" and "watsonx" in _clients:
        try: return _clients["watsonx"].model_id
        except Exception: return "granite"
    if provider == "gemini":  return GEMINI_MODEL_ID
    if provider == "groq":    return GROQ_MODEL_ID
    if provider == "openrouter": return OPENROUTER_MODEL
    return provider
