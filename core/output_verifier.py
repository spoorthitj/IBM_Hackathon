"""
Core — Output Verifier
Cross-agent consistency checks: downstream agents verify upstream outputs.
"""
import re

# Cyclone science ground-truth anchors
_PHYSICAL_RULES = [
    (r"pressure.*increas.*intensif",
     "Pressure DROPS during intensification, not increases"),
    (r"SST.*below\s+26.*cyclone",
     "Cyclones need SST ≥ 26°C"),
    (r"eye.*calm.*wall.*weak",
     "Eye WALL has the strongest winds, not the eye"),
    (r"wind.*decreas.*approach.*coast",
     "Winds typically strengthen near landfall before weakening inland"),
]

def verify_output(output: str, upstream_outputs: dict, agent_name: str) -> dict:
    """
    Verify an agent's output for:
    1. Physical plausibility (factual anchors)
    2. Consistency with upstream agent outputs
    Returns verification report dict.
    """
    issues    = []
    warnings  = []
    score     = 100.0

    # Physical rule checks
    for pattern, explanation in _PHYSICAL_RULES:
        if re.search(pattern, output, re.IGNORECASE):
            issues.append(f"Factual concern: {explanation}")
            score -= 15

    # Length check
    if len(output.strip()) < 100:
        warnings.append("Output is unusually short — may be incomplete")
        score -= 10

    # Cross-agent consistency
    if "weather" in upstream_outputs and agent_name == "Cyclone Detection Agent":
        weather_out = upstream_outputs["weather"].get("report", "")
        if "pressure" in weather_out.lower():
            wx_pressure = _extract_number(weather_out, r"(\d{3,4})\s*hPa")
            det_pressure = _extract_number(output, r"(\d{3,4})\s*hPa")
            if wx_pressure and det_pressure and abs(wx_pressure - det_pressure) > 20:
                warnings.append(
                    f"Pressure mismatch: Weather says {wx_pressure} hPa, Detection says {det_pressure} hPa")
                score -= 5

    if "detection" in upstream_outputs and agent_name == "Cyclone Tracking & Prediction Agent":
        det_out = upstream_outputs["detection"].get("report", "")
        if "deep depression" in det_out.lower() and "super cyclonic" in output.lower():
            warnings.append("Track agent claims Super Cyclonic but Detection only found Deep Depression")
            score -= 10

    score = max(0, min(100, round(score, 1)))
    passed = score >= 70 and len(issues) == 0

    return {
        "agent":    agent_name,
        "score":    score,
        "passed":   passed,
        "issues":   issues,
        "warnings": warnings,
        "label":    "✅ Verified" if passed else ("⚠️ Warning" if score >= 50 else "❌ Failed"),
    }


def _extract_number(text: str, pattern: str) -> float | None:
    m = re.search(pattern, text)
    try:
        return float(m.group(1)) if m else None
    except Exception:
        return None
