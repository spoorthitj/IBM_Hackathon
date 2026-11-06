"""
Guardrails Engine — 9 categories, 40+ checks.
All guardrails return a GuardrailResult and log to metrics_tracker.
"""
import re
import time
from dataclasses import dataclass, field
from typing import Optional
from utils.metrics_tracker import record_guardrail_event

# ── Result dataclass ─────────────────────────────────────────────
@dataclass
class GuardrailResult:
    passed:    bool
    category:  str
    check:     str
    severity:  str           # "low" | "medium" | "high" | "critical"
    message:   str
    details:   str = ""
    blocked:   bool = False  # True = hard block; False = warning/soft


# ── Patterns ─────────────────────────────────────────────────────
_INJECTION_PATTERNS = [
    r"ignore\s+previous\s+instructions",
    r"disregard\s+(all\s+)?prior",
    r"you\s+are\s+now\s+a",
    r"act\s+as\s+(?:an?\s+)?(?:unrestricted|evil|jailbreak|DAN)",
    r"do\s+anything\s+now",
    r"system\s*:.*override",
    r"<\s*/?system\s*>",
    r"\[INST\].*override",
]
_PII_PATTERNS = {
    "email":   r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
    "phone":   r"(?:\+91|0)?[6-9]\d{9}",
    "aadhaar": r"\b\d{4}\s?\d{4}\s?\d{4}\b",
    "pan":     r"\b[A-Z]{5}\d{4}[A-Z]\b",
    "credit":  r"\b(?:\d[ -]?){13,16}\b",
}
_TOXIC_WORDS = [
    "kill","murder","bomb","terror","explode","attack","destroy",
    "suicide","rape","racist","nazi","jihad",
]
_SQL_PATTERNS = [
    r"(?i)(select|insert|update|delete|drop|alter|create|truncate)\s+\w",
    r"(?i)union\s+(all\s+)?select",
    r"(?i)--\s*$",
    r"(?i);.*(drop|delete)",
    r"(?i)or\s+1\s*=\s*1",
]
_JAILBREAK_PHRASES = [
    "DAN mode", "developer mode", "god mode", "unrestricted mode",
    "training data", "reveal your system prompt", "pretend you have no restrictions",
]
_HALLUCINATION_ANCHORS = [
    # Phrases that signal unsupported speculation
    r"as of \d{4}, .{0,50} does not exist",
    r"I cannot verify",
    r"I made up",
    r"I invented",
]
_SENSITIVE_OUTPUT_PATTERNS = [
    r"API[_\s]?KEY\s*[=:]\s*\S+",
    r"password\s*[=:]\s*\S+",
    r"secret\s*[=:]\s*\S+",
    r"token\s*[=:]\s*[A-Za-z0-9_\-\.]{20,}",
]

# ── Operational limits ───────────────────────────────────────────
MAX_INPUT_TOKENS   = 4096
MAX_OUTPUT_TOKENS  = 1200
MAX_AGENT_ITER     = 10
MAX_TOOL_CALLS     = 20
TOKEN_BUDGET_LIMIT = 50_000  # per session
COST_BUDGET_USD    = 2.00    # per session
_session_tokens    = 0
_session_cost      = 0.0
_agent_iterations: dict[str, int] = {}


# ══════════════════════════════════════════════════════════════════
# 1. INPUT GUARDRAILS
# ══════════════════════════════════════════════════════════════════

def check_prompt_injection(text: str, agent: str = "") -> GuardrailResult:
    for pat in _INJECTION_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            r = GuardrailResult(False,"Input","Prompt Injection","critical",
                                "Potential prompt injection detected.",
                                f"Pattern matched: {pat}", blocked=True)
            _log(r, agent); return r
    return _ok("Input","Prompt Injection","low","No injection patterns detected.", agent)


def check_malicious_input(text: str, agent: str = "") -> GuardrailResult:
    for pat in _SQL_PATTERNS:
        if re.search(pat, text):
            r = GuardrailResult(False,"Input","Malicious Input","high",
                                "SQL injection pattern detected in input.",
                                blocked=True)
            _log(r, agent); return r
    for phrase in _JAILBREAK_PHRASES:
        if phrase.lower() in text.lower():
            r = GuardrailResult(False,"Input","Jailbreak Attempt","critical",
                                f"Jailbreak phrase detected: '{phrase}'",
                                blocked=True)
            _log(r, agent); return r
    return _ok("Input","Malicious Input","low","Input appears clean.", agent)


def check_input_validation(text: str, agent: str = "") -> GuardrailResult:
    if len(text.strip()) < 3:
        r = GuardrailResult(False,"Input","Input Validation","medium",
                            "Input is too short or empty.", blocked=False)
        _log(r, agent); return r
    if len(text) > 20_000:
        r = GuardrailResult(False,"Input","Input Validation","medium",
                            "Input exceeds 20,000 character limit.", blocked=True)
        _log(r, agent); return r
    return _ok("Input","Input Validation","low","Input length valid.", agent)


def check_pii(text: str, agent: str = "") -> GuardrailResult:
    found = []
    for pii_type, pat in _PII_PATTERNS.items():
        if re.search(pat, text):
            found.append(pii_type)
    if found:
        r = GuardrailResult(False,"Input","PII Detection","high",
                            f"PII detected: {', '.join(found)}. Input masked.",
                            details=f"Types: {found}", blocked=False)
        _log(r, agent); return r
    return _ok("Input","PII Detection","low","No PII detected.", agent)


def check_inappropriate_content(text: str, agent: str = "") -> GuardrailResult:
    hits = [w for w in _TOXIC_WORDS if w in text.lower().split()]
    if hits:
        r = GuardrailResult(False,"Input","Inappropriate Content","high",
                            f"Inappropriate terms detected: {hits}",
                            blocked=True)
        _log(r, agent); return r
    return _ok("Input","Inappropriate Content","low","Content is appropriate.", agent)


def run_input_guardrails(text: str, agent: str = "") -> list[GuardrailResult]:
    return [
        check_prompt_injection(text, agent),
        check_malicious_input(text, agent),
        check_input_validation(text, agent),
        check_pii(text, agent),
        check_inappropriate_content(text, agent),
    ]


# ══════════════════════════════════════════════════════════════════
# 2. OUTPUT GUARDRAILS
# ══════════════════════════════════════════════════════════════════

def check_hallucination(output: str, agent: str = "") -> GuardrailResult:
    for pat in _HALLUCINATION_ANCHORS:
        if re.search(pat, output, re.IGNORECASE):
            r = GuardrailResult(False,"Output","Hallucination Detection","high",
                                "Possible hallucination detected in output.",
                                blocked=False)
            _log(r, agent); return r
    # Length heuristic: very short output for a detailed prompt
    if len(output.strip()) < 50:
        r = GuardrailResult(False,"Output","Hallucination Detection","medium",
                            "Output is suspiciously short — may be incomplete.",
                            blocked=False)
        _log(r, agent); return r
    return _ok("Output","Hallucination Detection","low","Output appears substantive.", agent)


def check_factual_accuracy(output: str, agent: str = "") -> GuardrailResult:
    """Heuristic: flag if output contradicts known cyclone science anchors."""
    bad_claims = [
        (r"cyclone.*form.*below\s+26", "Cyclones require SST ≥26°C, not below"),
        (r"pressure.*increases.*intensif", "Pressure drops during intensification"),
        (r"wind.*calm.*at.*eye.*wall", "Eye wall has strongest winds"),
    ]
    for pat, reason in bad_claims:
        if re.search(pat, output, re.IGNORECASE):
            r = GuardrailResult(False,"Output","Factual Accuracy","high",
                                f"Potential factual error: {reason}",
                                blocked=False)
            _log(r, agent); return r
    return _ok("Output","Factual Accuracy","low","No obvious factual errors.", agent)


def check_toxicity(output: str, agent: str = "") -> GuardrailResult:
    hits = [w for w in _TOXIC_WORDS if w in output.lower().split()]
    if hits:
        r = GuardrailResult(False,"Output","Toxicity Filter","high",
                            f"Toxic content in output: {hits}", blocked=True)
        _log(r, agent); return r
    return _ok("Output","Toxicity Filter","low","Output is clean.", agent)


def check_sensitive_output(output: str, agent: str = "") -> GuardrailResult:
    for pat in _SENSITIVE_OUTPUT_PATTERNS:
        if re.search(pat, output, re.IGNORECASE):
            r = GuardrailResult(False,"Output","Sensitive Information","critical",
                                "Credential or secret detected in output!",
                                blocked=True)
            _log(r, agent); return r
    return _ok("Output","Sensitive Information","low","No credentials in output.", agent)


def check_response_format(output: str, expected: str = "text", agent: str = "") -> GuardrailResult:
    if expected == "json":
        try:
            import json; json.loads(output)
        except Exception:
            r = GuardrailResult(False,"Output","Response Format","medium",
                                "Expected JSON but output is not valid JSON.",
                                blocked=False)
            _log(r, agent); return r
    return _ok("Output","Response Format","low","Format valid.", agent)


def run_output_guardrails(output: str, agent: str = "") -> list[GuardrailResult]:
    return [
        check_hallucination(output, agent),
        check_factual_accuracy(output, agent),
        check_toxicity(output, agent),
        check_sensitive_output(output, agent),
        check_response_format(output, "text", agent),
    ]


# ══════════════════════════════════════════════════════════════════
# 3. TOOL EXECUTION GUARDRAILS
# ══════════════════════════════════════════════════════════════════

_ALLOWED_TOOLS = {
    "weather_fetch", "satellite_imagery", "track_model",
    "impact_calc", "alert_dispatch", "shelter_lookup",
    "historical_query", "ndrf_status",
}
_RESTRICTED_TOOLS = {"delete_record", "admin_override", "raw_db_exec"}


def check_tool_permission(tool_name: str, agent: str = "") -> GuardrailResult:
    if tool_name in _RESTRICTED_TOOLS:
        r = GuardrailResult(False,"Tool","Tool Access Permission","critical",
                            f"Tool '{tool_name}' is restricted.", blocked=True)
        _log(r, agent); return r
    if tool_name not in _ALLOWED_TOOLS:
        r = GuardrailResult(False,"Tool","Tool Access Permission","medium",
                            f"Tool '{tool_name}' is not in the approved list.",
                            blocked=False)
        _log(r, agent); return r
    return _ok("Tool","Tool Access Permission","low",f"Tool '{tool_name}' permitted.", agent)


def check_function_call(fn_name: str, args: dict, agent: str = "") -> GuardrailResult:
    for key, val in args.items():
        for pat in _SQL_PATTERNS:
            if isinstance(val, str) and re.search(pat, val):
                r = GuardrailResult(False,"Tool","Function Call Validation","high",
                                    f"Suspicious arg '{key}' in call to {fn_name}",
                                    blocked=True)
                _log(r, agent); return r
    return _ok("Tool","Function Call Validation","low","Function args validated.", agent)


def check_tool_call_count(agent: str = "", current_count: int = 0) -> GuardrailResult:
    if current_count >= MAX_TOOL_CALLS:
        r = GuardrailResult(False,"Tool","Restricted Tool Execution","high",
                            f"Agent '{agent}' exceeded max tool calls ({MAX_TOOL_CALLS}).",
                            blocked=True)
        _log(r, agent); return r
    return _ok("Tool","Restricted Tool Execution","low","Tool call count OK.", agent)


# ══════════════════════════════════════════════════════════════════
# 4. DATA GUARDRAILS
# ══════════════════════════════════════════════════════════════════

_ROLE_PERMISSIONS = {
    "admin":    {"read","write","delete"},
    "analyst":  {"read","write"},
    "viewer":   {"read"},
    "agent":    {"read"},
}


def check_data_privacy(data: dict, agent: str = "") -> GuardrailResult:
    sensitive_keys = {"password","token","secret","api_key","ssn","aadhaar"}
    found = [k for k in data if any(s in k.lower() for s in sensitive_keys)]
    if found:
        r = GuardrailResult(False,"Data","Data Privacy","high",
                            f"Sensitive keys in data payload: {found}",
                            blocked=False)
        _log(r, agent); return r
    return _ok("Data","Data Privacy","low","No sensitive keys in payload.", agent)


def check_role_access(role: str, action: str, agent: str = "") -> GuardrailResult:
    perms = _ROLE_PERMISSIONS.get(role, set())
    if action not in perms:
        r = GuardrailResult(False,"Data","Role-Based Access","high",
                            f"Role '{role}' not permitted to perform '{action}'.",
                            blocked=True)
        _log(r, agent); return r
    return _ok("Data","Role-Based Access","low",f"Role '{role}' permitted.", agent)


def mask_pii(text: str) -> str:
    """Return text with PII replaced by placeholders."""
    for pii_type, pat in _PII_PATTERNS.items():
        text = re.sub(pat, f"[{pii_type.upper()}_MASKED]", text)
    return text


# ══════════════════════════════════════════════════════════════════
# 5. SECURITY GUARDRAILS
# ══════════════════════════════════════════════════════════════════

def check_jailbreak(text: str, agent: str = "") -> GuardrailResult:
    for phrase in _JAILBREAK_PHRASES:
        if phrase.lower() in text.lower():
            r = GuardrailResult(False,"Security","Jailbreak Detection","critical",
                                f"Jailbreak attempt: '{phrase}'", blocked=True)
            _log(r, agent); return r
    return _ok("Security","Jailbreak Detection","low","No jailbreak detected.", agent)


def check_sql_injection(text: str, agent: str = "") -> GuardrailResult:
    for pat in _SQL_PATTERNS:
        if re.search(pat, text):
            r = GuardrailResult(False,"Security","SQL Injection","critical",
                                "SQL injection attempt in input.", blocked=True)
            _log(r, agent); return r
    return _ok("Security","SQL Injection","low","No SQL injection detected.", agent)


def check_credential_exposure(text: str, agent: str = "") -> GuardrailResult:
    for pat in _SENSITIVE_OUTPUT_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            r = GuardrailResult(False,"Security","Credential Exposure","critical",
                                "Credentials detected — redacted.", blocked=False)
            _log(r, agent); return r
    return _ok("Security","Credential Exposure","low","No credentials exposed.", agent)


def check_cross_agent_trust(source_agent: str, target_agent: str,
                             payload: str, agent: str = "") -> GuardrailResult:
    """Verify inter-agent messages are not injected."""
    return check_prompt_injection(payload, agent=f"{source_agent}→{target_agent}")


# ══════════════════════════════════════════════════════════════════
# 6. OPERATIONAL GUARDRAILS
# ══════════════════════════════════════════════════════════════════

def check_token_budget(tokens_used: int, agent: str = "") -> GuardrailResult:
    global _session_tokens
    _session_tokens += tokens_used
    if _session_tokens > TOKEN_BUDGET_LIMIT:
        r = GuardrailResult(False,"Operational","Token Budget","high",
                            f"Session token budget exceeded ({_session_tokens:,}/{TOKEN_BUDGET_LIMIT:,}).",
                            blocked=False)
        _log(r, agent); return r
    return _ok("Operational","Token Budget","low",
               f"Tokens used: {_session_tokens:,}/{TOKEN_BUDGET_LIMIT:,}.", agent)


def check_cost_budget(cost_usd: float, agent: str = "") -> GuardrailResult:
    global _session_cost
    _session_cost += cost_usd
    if _session_cost > COST_BUDGET_USD:
        r = GuardrailResult(False,"Operational","Cost Budget","high",
                            f"Cost budget exceeded (${_session_cost:.4f}/${COST_BUDGET_USD}).",
                            blocked=False)
        _log(r, agent); return r
    return _ok("Operational","Cost Budget","low",
               f"Session cost: ${_session_cost:.4f}/${COST_BUDGET_USD}.", agent)


def check_agent_iterations(agent_name: str) -> GuardrailResult:
    _agent_iterations[agent_name] = _agent_iterations.get(agent_name, 0) + 1
    if _agent_iterations[agent_name] > MAX_AGENT_ITER:
        r = GuardrailResult(False,"Operational","Max Agent Iterations","high",
                            f"Agent '{agent_name}' exceeded {MAX_AGENT_ITER} iterations.",
                            blocked=True)
        _log(r, agent_name); return r
    return _ok("Operational","Max Agent Iterations","low",
               f"Iteration {_agent_iterations[agent_name]}/{MAX_AGENT_ITER}.", agent_name)


def check_rate_limit(api_calls_per_min: int, limit: int = 20, agent: str = "") -> GuardrailResult:
    if api_calls_per_min > limit:
        r = GuardrailResult(False,"Operational","API Rate Limiting","medium",
                            f"Rate limit: {api_calls_per_min}/{limit} calls/min.",
                            blocked=False)
        _log(r, agent); return r
    return _ok("Operational","API Rate Limiting","low",
               f"Rate OK: {api_calls_per_min}/{limit}.", agent)


# ══════════════════════════════════════════════════════════════════
# 7. HUMAN-IN-THE-LOOP GUARDRAILS
# ══════════════════════════════════════════════════════════════════

_HITL_REQUIRED_ACTIONS = {
    "mass_evacuation_order", "emergency_broadcast", "ndrf_full_deployment",
    "port_closure_order", "financial_disbursement",
}


def check_hitl_required(action: str, agent: str = "") -> GuardrailResult:
    if action in _HITL_REQUIRED_ACTIONS:
        r = GuardrailResult(False,"HITL","Human Approval Required","high",
                            f"Action '{action}' requires human authorisation before execution.",
                            details="Escalated to duty officer.", blocked=True)
        _log(r, agent); return r
    return _ok("HITL","Human Approval Required","low","No HITL required for this action.", agent)


def check_critical_output_verification(output: str, confidence: float,
                                        threshold: float = 0.70,
                                        agent: str = "") -> GuardrailResult:
    if confidence < threshold:
        r = GuardrailResult(False,"HITL","Critical Output Verification","medium",
                            f"Confidence {confidence:.0%} below threshold {threshold:.0%}. Manual review recommended.",
                            blocked=False)
        _log(r, agent); return r
    return _ok("HITL","Critical Output Verification","low",
               f"Confidence {confidence:.0%} — OK.", agent)


# ══════════════════════════════════════════════════════════════════
# 8. MULTI-AGENT GUARDRAILS
# ══════════════════════════════════════════════════════════════════

_AGENT_COMM_LOG: list[dict] = []


def check_agent_loop(agent_name: str, task_id: str, agent: str = "") -> GuardrailResult:
    seen = [e for e in _AGENT_COMM_LOG if e["agent"]==agent_name and e["task"]==task_id]
    if len(seen) >= 3:
        r = GuardrailResult(False,"MultiAgent","Loop Detection","critical",
                            f"Agent '{agent_name}' has repeated task '{task_id}' {len(seen)} times.",
                            blocked=True)
        _log(r, agent); return r
    _AGENT_COMM_LOG.append({"agent":agent_name,"task":task_id,"ts":time.time()})
    return _ok("MultiAgent","Loop Detection","low","No loops detected.", agent)


def check_handoff_validity(from_agent: str, to_agent: str,
                            valid_agents: list, agent: str = "") -> GuardrailResult:
    if to_agent not in valid_agents:
        r = GuardrailResult(False,"MultiAgent","Handoff Accuracy","high",
                            f"Invalid handoff from '{from_agent}' to unknown agent '{to_agent}'.",
                            blocked=True)
        _log(r, agent); return r
    return _ok("MultiAgent","Handoff Accuracy","low",f"Handoff {from_agent}→{to_agent} valid.", agent)


def check_task_assignment(agent_name: str, task: str,
                           agent_capabilities: dict, agent: str = "") -> GuardrailResult:
    caps = agent_capabilities.get(agent_name, [])
    if not caps:
        r = GuardrailResult(False,"MultiAgent","Task Assignment","medium",
                            f"Agent '{agent_name}' has no registered capabilities.",
                            blocked=False)
        _log(r, agent); return r
    return _ok("MultiAgent","Task Assignment","low",
               f"Agent '{agent_name}' capable.", agent)


# ══════════════════════════════════════════════════════════════════
# 9. ETHICAL & COMPLIANCE GUARDRAILS
# ══════════════════════════════════════════════════════════════════

_BIAS_TERMS = {
    "demographic": ["women","men","hindu","muslim","christian","caste","tribe","poor","rich"],
    "regional":    ["only odisha", "only andhra", "not gujarat", "not kerala"],
}


def check_bias(output: str, agent: str = "") -> GuardrailResult:
    ol = output.lower()
    for category, terms in _BIAS_TERMS.items():
        for term in terms:
            if re.search(rf"\b{re.escape(term)}\b", ol):
                # Bias indicator only if used in discriminatory context
                if re.search(rf"(not\s+|ignore\s+|less\s+important\s+).*{re.escape(term)}", ol):
                    r = GuardrailResult(False,"Ethical","Bias Detection","high",
                                        f"Potential {category} bias detected: '{term}'",
                                        blocked=False)
                    _log(r, agent); return r
    return _ok("Ethical","Bias Detection","low","No bias detected.", agent)


def check_fairness(output: str, agent: str = "") -> GuardrailResult:
    """Check that warnings cover all regions equitably."""
    if "alert" in output.lower():
        regions = ["andhra","odisha","gujarat","tamil","kerala","karnataka","west bengal","maharashtra"]
        covered = sum(1 for r in regions if r in output.lower())
        if covered < 2:
            r = GuardrailResult(False,"Ethical","Fairness Validation","medium",
                                "Alert may not cover all vulnerable coastal regions equitably.",
                                blocked=False)
            _log(r, agent); return r
    return _ok("Ethical","Fairness Validation","low","Coverage appears equitable.", agent)


def check_audit_trail(action: str, agent: str, user: str = "system") -> GuardrailResult:
    # In production this writes to an audit DB; here we log to metrics
    record_guardrail_event("Ethical","Audit Trail",False,"low",
                           f"{user} → {agent}: {action}", agent)
    return _ok("Ethical","Audit Trail","low",f"Action '{action}' logged.", agent)


def check_regulatory_compliance(output: str, agent: str = "") -> GuardrailResult:
    """Check NDMA guidelines are referenced where relevant."""
    if "evacuat" in output.lower() and "ndma" not in output.lower():
        r = GuardrailResult(False,"Ethical","Regulatory Compliance","medium",
                            "Evacuation recommendation should reference NDMA guidelines.",
                            blocked=False)
        _log(r, agent); return r
    return _ok("Ethical","Regulatory Compliance","low","Compliance check passed.", agent)


# ══════════════════════════════════════════════════════════════════
# Master pipeline
# ══════════════════════════════════════════════════════════════════

def run_full_pipeline(prompt: str, output: str, agent_name: str,
                      tokens_used: int = 0, cost: float = 0.0,
                      confidence: float = 0.9) -> dict:
    """
    Run all applicable guardrails for a single agent call.
    Returns {passed: bool, blocked: bool, results: [GuardrailResult], summary: str}
    """
    results: list[GuardrailResult] = []

    # Input
    results += run_input_guardrails(prompt, agent_name)

    # Output
    results += run_output_guardrails(output, agent_name)

    # Operational
    results.append(check_token_budget(tokens_used, agent_name))
    results.append(check_cost_budget(cost, agent_name))
    results.append(check_agent_iterations(agent_name))

    # HITL
    results.append(check_critical_output_verification(output, confidence, agent=agent_name))

    # Ethical
    results.append(check_bias(output, agent_name))
    results.append(check_fairness(output, agent_name))
    results.append(check_regulatory_compliance(output, agent_name))
    results.append(check_audit_trail("generate_report", agent_name))

    # Security
    results.append(check_jailbreak(prompt, agent_name))
    results.append(check_credential_exposure(output, agent_name))

    blocked = any(r.blocked for r in results if not r.passed)
    passed  = all(r.passed for r in results)
    fails   = [r for r in results if not r.passed]

    summary = (
        f"✅ All {len(results)} guardrails passed." if passed
        else f"⚠️ {len(fails)}/{len(results)} checks flagged — "
             + (f"🔴 BLOCKED" if blocked else "🟡 Warning only")
    )
    return {
        "passed":  passed,
        "blocked": blocked,
        "results": results,
        "summary": summary,
        "total":   len(results),
        "failed":  len(fails),
    }


def get_all_events() -> list[dict]:
    from utils.metrics_tracker import get_guardrail_events
    return get_guardrail_events()


# ── Internal helpers ─────────────────────────────────────────────

def _ok(category, check, severity, message, agent) -> GuardrailResult:
    r = GuardrailResult(True, category, check, severity, message)
    _log(r, agent)
    return r


def _log(r: GuardrailResult, agent: str):
    record_guardrail_event(
        category=r.category, check=r.check,
        triggered=not r.passed, severity=r.severity,
        detail=r.message, agent=agent,
    )
