"""
Security — NeMo Guardrails Shim
Provides NeMo-style Colang rail interface.
Falls back gracefully if nemoguardrails package is not installed.
"""
import re

# NeMo Colang-style rail definitions for cyclone domain
COLANG_CONFIG = """
define user ask about cyclone
  "cyclone"
  "storm"
  "hurricane"
  "weather alert"

define bot respond about cyclone
  "I'll analyze the cyclone data and provide a safety assessment."

define flow cyclone safety
  user ask about cyclone
  bot respond about cyclone

define user jailbreak attempt
  "ignore previous"
  "disregard instructions"
  "you are now"
  "act as"
  "DAN mode"
  "developer mode"

define bot refuse jailbreak
  "I'm a cyclone safety AI. I cannot change my core safety mission."

define flow jailbreak prevention
  user jailbreak attempt
  bot refuse jailbreak
"""

_INJECTION_RE = [
    r"ignore\s+(previous|prior|all)\s+instructions",
    r"you\s+are\s+now\s+(?:an?\s+)?(?:unrestricted|evil|DAN)",
    r"act\s+as\s+(?:an?\s+)?(?:uncensored|jailbreak)",
    r"disregard\s+(?:your|all)\s+(?:instructions|guidelines)",
    r"developer\s+mode",
    r"DAN\s+mode",
]


class NeMoRails:
    """Lightweight NeMo Guardrails interface."""

    def __init__(self):
        self._nemo_available = False
        try:
            import nemoguardrails  # type: ignore
            self._nemo_available = True
        except ImportError:
            pass

    def check(self, user_input: str) -> dict:
        """
        Check user input against NeMo-style rails.
        Returns dict with: allowed (bool), reason (str), blocked_by (str).
        """
        for pattern in _INJECTION_RE:
            if re.search(pattern, user_input, re.IGNORECASE):
                return {
                    "allowed":    False,
                    "reason":     f"Jailbreak/injection pattern detected",
                    "blocked_by": "NeMo Rail: jailbreak_prevention",
                    "severity":   "critical",
                }

        if len(user_input.strip()) < 3:
            return {"allowed": False, "reason": "Input too short",
                    "blocked_by": "NeMo Rail: input_validation", "severity": "low"}

        off_topic_re = r"\b(politics|religion|sports|stock|crypto|porn|violence)\b"
        if re.search(off_topic_re, user_input, re.IGNORECASE):
            return {"allowed": False, "reason": "Off-topic content for cyclone safety system",
                    "blocked_by": "NeMo Rail: topic_filter", "severity": "medium"}

        return {"allowed": True, "reason": "Passed all NeMo rails",
                "blocked_by": None, "severity": "none"}

    def get_config(self) -> str:
        return COLANG_CONFIG

    @property
    def is_native(self) -> bool:
        return self._nemo_available


# Singleton instance
_rails = None


def get_rails() -> NeMoRails:
    global _rails
    if _rails is None:
        _rails = NeMoRails()
    return _rails
