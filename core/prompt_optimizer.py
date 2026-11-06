"""
Core — Prompt Optimizer
Compresses prompts, tracks token savings, applies domain-aware optimizations.
"""
import re

# Domain-specific abbreviation map
_ABBREV = {
    "atmospheric pressure": "pressure",
    "sea surface temperature": "SST",
    "wind speed": "wind",
    "relative humidity": "humidity",
    "cyclone detection & early warning system": "CDEWS",
    "india meteorological department": "IMD",
    "national disaster management authority": "NDMA",
    "national disaster response force": "NDRF",
    "extremely severe cyclonic storm": "ESCS",
    "very severe cyclonic storm": "VSCS",
    "cyclonic storm": "CS",
}

_REDUNDANT_PHRASES = [
    r"please\s+", r"kindly\s+", r"I\s+want\s+you\s+to\s+",
    r"can\s+you\s+please\s+", r"I\s+need\s+you\s+to\s+",
]


def optimize(prompt: str) -> tuple[str, int, int]:
    """
    Compress a prompt. Returns (optimized_prompt, original_tokens, new_tokens).
    """
    original = prompt
    # Remove redundant politeness phrases
    for pat in _REDUNDANT_PHRASES:
        prompt = re.sub(pat, "", prompt, flags=re.IGNORECASE)

    # Remove duplicate blank lines
    prompt = re.sub(r"\n{3,}", "\n\n", prompt)

    # Apply abbreviations (only in data sections, not instructions)
    for full, abbr in _ABBREV.items():
        if full.lower() in prompt.lower():
            prompt = re.sub(re.escape(full), abbr, prompt, flags=re.IGNORECASE, count=2)

    orig_tokens = _estimate_tokens(original)
    new_tokens  = _estimate_tokens(prompt)
    return prompt, orig_tokens, new_tokens


def _estimate_tokens(text: str) -> int:
    try:
        import tiktoken
        return len(tiktoken.get_encoding("cl100k_base").encode(text))
    except Exception:
        return int(len(text.split()) * 1.3)


def optimization_ratio(orig: int, new: int) -> float:
    if orig == 0:
        return 0.0
    return round((orig - new) / orig * 100, 1)
