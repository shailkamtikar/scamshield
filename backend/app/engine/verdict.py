"""
Deterministic verdict, score and confidence.

Verdicts: SAFE, SUSPICIOUS, DANGEROUS, COULD_NOT_VERIFY.
Gemini never sets or changes any value computed here.
"""

from dataclasses import dataclass, field

from app.engine.signals import Signal, dedupe

BANDS = {"SAFE": (0, 19), "SUSPICIOUS": (20, 59), "DANGEROUS": (60, 100)}
DECISIVE_IDS = {"FEED_HIT", "VT_MALICIOUS_MANY", "DANGEROUS_SCHEME", "HOST_FLAGGED_PAGE", "SANDBOX_MALICIOUS"}
# Structural evidence that a link is fake. Any one of these on a site that is
# not on a trusted list makes the link DANGEROUS on its own.
FAKE_IDS = {
    "DOMAIN_GIBBERISH", "HOMOGRAPH", "INVISIBLE_CHARS", "USERINFO_TRICK",
    "RAW_IP", "OBFUSCATED_IP", "BRAND_LOOKALIKE", "BRAND_COMBOSQUAT",
    "BRAND_MISMATCH_PAGE",
    "UPI_BRAND_PAYEE_MISMATCH",
}
UNREACHABLE = {"NXDOMAIN", "CONNECT_FAILED", "TIMEOUT", "NOT_FOUND", "TLS_ERROR", "LOOP", "TOO_MANY_HOPS"}


def risk_level_for(verdict: str, score: int | None) -> str:
    if verdict == "COULD_NOT_VERIFY":
        return "UNKNOWN"
    if verdict == "SAFE":
        return "LOW"
    if verdict == "SUSPICIOUS":
        return "MEDIUM" if (score or 0) < 40 else "HIGH"
    return "CRITICAL" if (score or 0) >= 80 else "HIGH"


@dataclass
class Assessment:
    verdict: str
    score: int | None
    rule: str
    risk_points: int
    trust_points: int
    signals: list[Signal] = field(default_factory=list)


def clamp_to_band(verdict: str, raw: int) -> int:
    lo, hi = BANDS[verdict]
    return max(lo, min(hi, raw))


def assess_url(
    signals: list[Signal],
    trust_tier: str,
    fetch_outcome: str | None,
    platform: bool = False,
) -> Assessment:
    """Decide the verdict for ONE link. Rules are evaluated in order."""

    sigs = dedupe(signals)
    risk = sum(s.points for s in sigs if s.polarity == "risk")
    trust = sum(s.points for s in sigs if s.polarity == "trust")
    ids = {s.id for s in sigs if s.polarity == "risk"}

    def result(verdict: str, rule: str, raw: int) -> Assessment:
        score = None if verdict == "COULD_NOT_VERIFY" else clamp_to_band(verdict, raw)
        return Assessment(verdict, score, rule, risk, trust, sigs)

    # Several tiny oddities are not evidence of a scam: without at least one
    # moderate signal, a link needs a clearly higher total to be flagged.
    substantial = any(s.polarity == "risk" and s.strength != "weak" for s in sigs)
    flag_at = 20 if substantial else 30

    if ids & DECISIVE_IDS:
        return result("DANGEROUS", "R1_THREAT_INTEL_OR_DECISIVE", max(risk, 92))

    official_or_popular = trust_tier in {"OFFICIAL", "POPULAR"}

    if not official_or_popular and (ids & FAKE_IDS):
        return result("DANGEROUS", "R2_FAKE_STRUCTURE", max(risk, 70))
    if risk >= 60:
        return result("DANGEROUS", "R2_RISK_SUM", risk)

    if fetch_outcome in UNREACHABLE and trust_tier != "OFFICIAL" and risk < 20:
        return result("COULD_NOT_VERIFY", "R3_UNREACHABLE", 0)

    if trust_tier == "OFFICIAL":
        return result("SAFE", "R4_OFFICIAL_DOMAIN", min(risk, 10))

    if trust_tier == "POPULAR":
        if risk < flag_at:
            return result("SAFE", "R5_POPULAR_CLEAN", min(risk, 15))
        return result("SUSPICIOUS", "R5_POPULAR_WITH_RISK", risk)

    if platform:
        return result("SUSPICIOUS", "R6_UNVERIFIED_HOSTING", max(risk, 25))
    if risk >= flag_at:
        return result("SUSPICIOUS", "R6_UNKNOWN_WITH_RISK", risk)
    return result("SAFE", "R7_UNKNOWN_NO_RISK", min(risk, 18))


# ---------------------------------------------------------------- confidence
CHECK_WEIGHTS = {
    "message_rules": 2.0, "qr_payload": 2.0,
    "lexical": 2.0, "trust": 2.0, "google_safe_browsing": 2.0, "openphish": 1.0,
    "urlhaus": 1.0, "virustotal": 1.0, "phishing_database": 1.0, "reachability": 2.0, "domain_age": 1.0, "page": 1.0, "sandbox": 2.0,
}


def confidence_for(
    verdict: str,
    signals: list[Signal],
    checks: dict[str, str],
    trust_tier: str,
) -> tuple[float, dict]:
    """
    confidence = clamp(0.25 + 0.40*coverage + 0.35*agreement)

    coverage:  weighted share of applicable checks that actually completed
    agreement: share of strong/decisive evidence that points the same way as
               the verdict
    `checks` maps check name -> done | unavailable | skipped (skipped = not
    applicable and excluded from coverage).
    """

    applicable = {k: v for k, v in checks.items() if v != "skipped"}
    total = sum(CHECK_WEIGHTS.get(k, 1.0) for k in applicable)
    done = sum(CHECK_WEIGHTS.get(k, 1.0) for k, v in applicable.items() if v == "done")
    coverage = done / total if total else 0.0

    vote = {"decisive": 3, "strong": 2, "moderate": 1, "weak": 0.25}
    bad = sum(vote[s.strength] for s in signals if s.polarity == "risk")
    good = sum(vote[s.strength] for s in signals if s.polarity == "trust")
    if verdict in {"DANGEROUS", "SUSPICIOUS"}:
        agreement = bad / (bad + good) if (bad + good) else 0.5
    elif verdict == "SAFE":
        agreement = good / (good + bad) if (good + bad) else 0.5
    else:
        agreement = 0.4

    confidence = 0.25 + 0.40 * coverage + 0.35 * agreement

    decisive = any(s.strength == "decisive" and s.polarity == "risk" for s in signals)
    if decisive:
        confidence = max(confidence, 0.96)
    elif verdict == "SAFE" and trust_tier == "OFFICIAL" and bad == 0:
        confidence = max(confidence, 0.95)
    elif verdict == "SAFE" and trust_tier == "POPULAR" and bad == 0:
        confidence = max(confidence, 0.88)
    elif verdict == "SAFE" and trust_tier == "UNKNOWN":
        confidence = min(confidence, 0.75)
    if verdict == "COULD_NOT_VERIFY":
        confidence = min(confidence, 0.5)
    if coverage < 0.4:
        confidence = min(confidence, 0.6)

    missing = sorted(k for k, v in applicable.items() if v == "unavailable")
    factors = {
        "coverage": round(coverage, 2),
        "agreement": round(agreement, 2),
        "missing_checks": missing,
    }
    return round(max(0.05, min(0.99, confidence)), 2), factors
