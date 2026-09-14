from pydantic import BaseModel


class RiskSignal(BaseModel):
    """
    A single normalized, deterministic piece of risk evidence.

    `target` is the normalized subject the signal is ABOUT — a normalized
    URL/domain for URL-derived signals, or None for message-level signals
    (urgency, threats, ...). Two signals with the same (category, target)
    describe the SAME underlying fact and must be deduplicated rather than
    double-counted — this is what makes the same malicious URL contribute
    identically whether it arrived via text, OCR, or a QR code.
    """

    category: str
    points: int
    description: str
    source: str
    target: str | None = None


# Deterministic point value per signal category. This table is the ONLY
# place risk_score weights live — Gemini never sets or overrides these.
# Weights are evidence-strength judgments, not tuned to any single example:
#   - BRAND_IMPERSONATION / URL_RAW_IP are strong standalone indicators.
#   - CREDENTIAL_REQUEST / FEAR_OR_THREAT / FINANCIAL_PRESSURE are strong
#     social-engineering tactics.
#   - URGENCY / SUSPICIOUS_CALL_TO_ACTION / URL_SUSPICIOUS_KEYWORD /
#     URL_EXCESSIVE_SUBDOMAINS are common but weaker on their own.
#   - URL_INSECURE (no HTTPS) is a minor, easily-forged signal.
CATEGORY_POINTS: dict[str, int] = {
    "BRAND_IMPERSONATION": 35,
    "URL_RAW_IP": 25,
    "CREDENTIAL_REQUEST": 20,
    "FEAR_OR_THREAT": 15,
    "FINANCIAL_PRESSURE": 15,
    "URL_EXCESSIVE_SUBDOMAINS": 15,
    "URL_SUSPICIOUS_KEYWORD": 10,
    "URGENCY": 10,
    "SUSPICIOUS_CALL_TO_ACTION": 10,
    "URL_INSECURE": 5,
}

CATEGORY_LABELS: dict[str, str] = {
    "BRAND_IMPERSONATION": "Possible brand impersonation",
    "URL_RAW_IP": "URL uses a raw IP address",
    "CREDENTIAL_REQUEST": "Credential request",
    "FEAR_OR_THREAT": "Fear / threat language",
    "FINANCIAL_PRESSURE": "Financial pressure",
    "URL_EXCESSIVE_SUBDOMAINS": "Excessive subdomains",
    "URL_SUSPICIOUS_KEYWORD": "Suspicious URL keyword",
    "URGENCY": "Urgency language",
    "SUSPICIOUS_CALL_TO_ACTION": "Suspicious call to action",
    "URL_INSECURE": "Insecure (non-HTTPS) URL",
}


def make_signal(category: str, description: str, source: str, target: str | None = None) -> RiskSignal:
    return RiskSignal(
        category=category,
        points=CATEGORY_POINTS[category],
        description=description,
        source=source,
        target=target,
    )


def deduplicate_signals(signals: list[RiskSignal]) -> list[RiskSignal]:
    """
    Collapse signals that describe the SAME fact (same category + same
    normalized target) into one. This is what makes evidence for a given
    URL/domain converge no matter how many times or which modality it was
    observed through, and stops a repeated regex match from being counted
    twice.
    """

    seen: dict[tuple[str, str | None], RiskSignal] = {}
    for signal in signals:
        key = (signal.category, signal.target)
        if key not in seen:
            seen[key] = signal
    return list(seen.values())


# Deterministic risk_score -> risk_level thresholds. This is the single
# authoritative mapping used for the final `risk_level` returned to the
# client — Gemini's own opinion is informational only and can never
# override it, so risk_score and risk_level can never contradict each
# other. Reasoning:
#   0      -> LOW        no negative signal fired at all
#   1-39   -> MEDIUM      a single weak/moderate signal (e.g. just "urgency")
#   40-69  -> HIGH        a strong standalone signal (e.g. a lookalike
#                          domain) or several moderate ones together
#   70-100 -> CRITICAL     multiple corroborating strong signals (e.g. a
#                          lookalike domain AND social-engineering language)
def derive_risk_level(risk_score: int) -> str:
    if risk_score >= 70:
        return "CRITICAL"
    if risk_score >= 40:
        return "HIGH"
    if risk_score >= 1:
        return "MEDIUM"
    return "LOW"
