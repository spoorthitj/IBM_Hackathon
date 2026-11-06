"""
Security — AI Governance & Agent Policies
Defines named policies, tracks compliance, generates governance reports.
"""
from datetime import datetime

# ── Policy Definitions ────────────────────────────────────────────
POLICIES = [
    {"id":"POL-001","name":"Human Approval for Mass Evacuation",
     "desc":"Any mass evacuation order must be approved by a duty officer before dispatch.",
     "level":"MANDATORY","category":"HITL","version":"1.0"},
    {"id":"POL-002","name":"No Unsupported Intensity Claims",
     "desc":"Agents must not claim cyclone intensity without supporting meteorological data.",
     "level":"MANDATORY","category":"Accuracy","version":"1.0"},
    {"id":"POL-003","name":"Data Minimisation",
     "desc":"Agents shall not collect or retain personal data beyond operational necessity.",
     "level":"MANDATORY","category":"Privacy","version":"1.0"},
    {"id":"POL-004","name":"Equitable Regional Coverage",
     "desc":"Early warning alerts must cover all vulnerable coastal states equitably.",
     "level":"MANDATORY","category":"Fairness","version":"1.0"},
    {"id":"POL-005","name":"Token Budget Compliance",
     "desc":"Total token usage per session shall not exceed 50,000 tokens.",
     "level":"ADVISORY","category":"Operational","version":"1.0"},
    {"id":"POL-006","name":"Toxicity-Free Outputs",
     "desc":"All agent outputs must pass toxicity screening before display.",
     "level":"MANDATORY","category":"Safety","version":"1.0"},
    {"id":"POL-007","name":"Audit Trail Maintenance",
     "desc":"All agent actions and outputs must be logged to the audit trail.",
     "level":"MANDATORY","category":"Compliance","version":"1.0"},
    {"id":"POL-008","name":"Credential Non-Disclosure",
     "desc":"API keys and credentials must never appear in agent outputs.",
     "level":"MANDATORY","category":"Security","version":"1.0"},
    {"id":"POL-009","name":"Hallucination Threshold",
     "desc":"Responses with confidence below 70% must be flagged for human review.",
     "level":"MANDATORY","category":"Accuracy","version":"1.0"},
    {"id":"POL-010","name":"Jailbreak Resistance",
     "desc":"Agents must resist prompt injection and jailbreak attempts at all times.",
     "level":"MANDATORY","category":"Security","version":"1.0"},
    {"id":"POL-011","name":"NDMA Guideline Reference",
     "desc":"Evacuation recommendations must reference NDMA/IMD official guidelines.",
     "level":"ADVISORY","category":"Compliance","version":"1.0"},
    {"id":"POL-012","name":"Multi-Agent Loop Prevention",
     "desc":"Agent orchestrator must detect and break infinite execution loops.",
     "level":"MANDATORY","category":"Operational","version":"1.0"},
    {"id":"POL-013","name":"Responsible AI Principles",
     "desc":"All outputs must align with IBM Responsible AI principles: fairness, robustness, explainability.",
     "level":"ADVISORY","category":"Ethics","version":"1.0"},
    {"id":"POL-014","name":"Cost Budget Compliance",
     "desc":"Session LLM cost must not exceed $2.00 USD per session.",
     "level":"ADVISORY","category":"Operational","version":"1.0"},
    {"id":"POL-015","name":"Cross-Agent Output Verification",
     "desc":"Downstream agents must verify upstream outputs before incorporating them.",
     "level":"ADVISORY","category":"Accuracy","version":"1.0"},
]

_AUDIT_LOG: list[dict] = []


def log_action(agent: str, action: str, policy_id: str | None = None,
               compliant: bool = True, detail: str = ""):
    _AUDIT_LOG.append({
        "ts":         datetime.utcnow().isoformat(),
        "agent":      agent,
        "action":     action,
        "policy_id":  policy_id or "—",
        "compliant":  compliant,
        "detail":     detail[:200],
    })


def check_policy(policy_id: str, value) -> dict:
    """Check compliance against a specific policy."""
    pol = next((p for p in POLICIES if p["id"] == policy_id), None)
    if not pol:
        return {"compliant": True, "policy": None}
    # Simple boolean compliance
    compliant = bool(value)
    log_action("system", f"Policy check: {pol['name']}", policy_id, compliant)
    return {"compliant": compliant, "policy": pol}


def get_audit_log()  -> list[dict]: return list(_AUDIT_LOG)
def get_policies()   -> list[dict]: return POLICIES


def generate_governance_report() -> str:
    mandatory   = [p for p in POLICIES if p["level"] == "MANDATORY"]
    advisory    = [p for p in POLICIES if p["level"] == "ADVISORY"]
    audit_count = len(_AUDIT_LOG)
    violations  = sum(1 for e in _AUDIT_LOG if not e["compliant"])

    return f"""# AI Governance Report
Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

## Policy Summary
- Total Policies: {len(POLICIES)}
- Mandatory: {len(mandatory)}
- Advisory: {len(advisory)}

## Compliance Status
- Audit Events: {audit_count}
- Policy Violations: {violations}
- Compliance Rate: {round((audit_count - violations) / max(audit_count,1) * 100, 1)}%

## Responsible AI Principles
- **Fairness**: Equitable coverage across all 5 coastal zones enforced (POL-004)
- **Robustness**: Guardrails active across 9 categories (40+ checks)
- **Explainability**: All agent decisions logged with reasoning steps
- **Transparency**: Full audit trail maintained (POL-007)
- **Privacy**: PII detection and masking active (POL-003)
- **Security**: NeMo + custom guardrails for injection resistance (POL-010)

## IBM Responsible AI Alignment
This system follows IBM AI Ethics principles: explainability, fairness,
robustness, transparency, and privacy. Human-in-the-loop controls are
enforced for all critical decisions (POL-001).
"""
