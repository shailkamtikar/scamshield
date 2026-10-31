"""
The investigation pipeline as plain steps over a `Case`. The LangGraph in
app/graph/graph.py wires these steps together; they are also directly
callable (used by the benchmark and the tests).
"""

import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from app.engine import message as msg_engine
from app.engine import verdict as V
from app.engine.signals import WEIGHTS_VERSION, Signal, dedupe, make
from app.engine.url_analysis import UrlReport, analyze_url
from app.intel.trust import brand_tokens
from app.intel.urls import ParsedUrl, extract_urls

MAX_URLS = 6
SEV = {"SAFE": 0, "COULD_NOT_VERIFY": 1, "SUSPICIOUS": 2, "DANGEROUS": 3}
RISKY_CONTEXT_IDS = {
    "URGENCY", "FEAR_OR_THREAT", "CREDENTIAL_REQUEST", "KYC_UPDATE", "FINANCIAL_PRESSURE",
    "SUSPICIOUS_CTA", "PRIZE_LOTTERY", "ARREST_THREAT", "JOB_TASK_SCAM", "APK_INSTALL",
}


@dataclass
class Case:
    message: str
    claimed_organization: str | None = None
    source: str = "web"
    kind: str = "text"  # text | image | qr
    network: bool | None = None
    extra_signals: list[Signal] = field(default_factory=list)  # e.g. from QR payload analysis
    extra: dict = field(default_factory=dict)  # kind specific info shown in the response

    urls: list[ParsedUrl] = field(default_factory=list)
    skipped_urls: list[str] = field(default_factory=list)
    msg: msg_engine.MessageAnalysis | None = None
    url_reports: list[UrlReport] = field(default_factory=list)
    result: dict = field(default_factory=dict)
    signals: list[Signal] = field(default_factory=list)


# ------------------------------------------------------------------ steps
def step_extract(case: Case) -> Case:
    found = extract_urls(case.message, limit=40)
    case.urls = found[:MAX_URLS]
    case.skipped_urls = [u.url for u in found[MAX_URLS:]]
    return case


def step_message(case: Case) -> Case:
    case.msg = msg_engine.analyze(case.message, case.claimed_organization, case.source)
    return case


def _expected_brands(case: Case):
    brands = list(case.msg.mentioned_brands) if case.msg else []
    if case.claimed_organization:
        squashed = re.sub(r"[^a-z0-9]", "", case.claimed_organization.lower())
        brand = brand_tokens().get(squashed)
        if brand and brand not in brands:
            brands.append(brand)
    return tuple(brands)


def step_urls(case: Case) -> Case:
    extra = (case.claimed_organization,) if case.claimed_organization else ()
    risky = bool(case.msg and any(s.id in RISKY_CONTEXT_IDS for s in case.msg.signals))
    expected = _expected_brands(case)

    def run(parsed: ParsedUrl) -> UrlReport:
        return analyze_url(parsed, network=case.network, extra_brands=extra, expected_brands=expected, risky_context=risky)

    if len(case.urls) <= 1:
        case.url_reports = [run(u) for u in case.urls]
    else:
        with ThreadPoolExecutor(max_workers=min(4, len(case.urls))) as pool:
            case.url_reports = list(pool.map(run, case.urls))
    return case


def step_decide(case: Case) -> Case:
    msg_signals = list(case.msg.signals if case.msg else []) + case.extra_signals
    msg_signals = dedupe(msg_signals)
    ids = {s.id for s in msg_signals if s.polarity == "risk"}
    raw_msg_risk = sum(s.points for s in msg_signals if s.polarity == "risk")
    genuine = any(s.id == "GENUINE_ALERT_PATTERN" for s in msg_signals)
    msg_risk = max(0, raw_msg_risk - (15 if genuine else 0))

    path: list[str] = []
    msg_verdict = "SAFE"
    if ids & V.DECISIVE_IDS:
        msg_verdict = "DANGEROUS"
        path.append("M1_DECISIVE_MESSAGE_SIGNAL")
    elif "CREDENTIAL_REQUEST" in ids and ids & {"URGENCY", "FEAR_OR_THREAT", "ARREST_THREAT", "KYC_UPDATE", "SUSPICIOUS_CTA"}:
        msg_verdict = "DANGEROUS"
        path.append("M2_CREDENTIAL_REQUEST_UNDER_PRESSURE")
    elif "ARREST_THREAT" in ids and ids & {"FEAR_OR_THREAT", "PHONE_CALL_TO_ACTION", "URGENCY", "FINANCIAL_PRESSURE"}:
        msg_verdict = "DANGEROUS"
        path.append("M3_ARREST_THREAT")
    elif ids & V.FAKE_IDS:
        msg_verdict = "DANGEROUS"
        path.append("M7_IMPERSONATION_SIGNAL")
    elif ids & {"UPI_COLLECT_SCAM", "REMOTE_ACCESS_APP"}:
        msg_verdict = "DANGEROUS"
        path.append("M4_COLLECT_OR_REMOTE_ACCESS")
    elif msg_risk >= 55:
        msg_verdict = "DANGEROUS"
        path.append("M5_MESSAGE_RISK_SUM")
    elif msg_risk >= 20:
        msg_verdict = "SUSPICIOUS"
        path.append("M6_MESSAGE_RISK")

    reports = case.url_reports
    worst = max(reports, key=lambda r: (SEV[r.verdict], r.score or 0), default=None)
    url_verdict = worst.verdict if worst else "SAFE"

    verdict = "SAFE"
    score_raw = 0
    deciding: UrlReport | None = None
    if url_verdict == "DANGEROUS":
        verdict, deciding = "DANGEROUS", worst
        score_raw = max(worst.score or 60, msg_risk)
        path.append(f"U:{worst.rule}")
    elif msg_verdict == "DANGEROUS":
        verdict = "DANGEROUS"
        url_part = max((r.risk_points for r in reports if r.verdict != "COULD_NOT_VERIFY"), default=0)
        score_raw = max(70, msg_risk + url_part)
        deciding = worst
    else:
        url_part = max((r.risk_points for r in reports if r.verdict != "COULD_NOT_VERIFY"), default=0)
        total = url_part + msg_risk
        if total >= 60:
            verdict = "DANGEROUS"
            path.append("C1_MESSAGE_AND_LINK_COMBINED")
            score_raw, deciding = total, worst
        elif total >= 20:
            verdict = "SUSPICIOUS"
            path.append(f"U:{worst.rule}" if (worst and url_part) else "C2_COMBINED_RISK")
            score_raw, deciding = total, worst
        elif url_verdict == "COULD_NOT_VERIFY":
            verdict, deciding = "COULD_NOT_VERIFY", worst
            path.append(f"U:{worst.rule}")
        else:
            verdict, deciding = "SAFE", worst
            score_raw = total
            path.append(f"U:{worst.rule}" if worst else "M0_NO_RISK_FOUND")

    score = None if verdict == "COULD_NOT_VERIFY" else V.clamp_to_band(verdict, int(score_raw))

    # QR codes that lead to a verified official service
    if case.kind == "qr" and reports and reports[0].trust["tier"] == "OFFICIAL" and verdict == "SAFE":
        t = reports[0].trust
        msg_signals.append(make("VERIFIED_SERVICE", f"The QR points to {t['brand']} (verified official domain).", "qr"))
        if isinstance(case.extra.get("qr"), dict):
            case.extra["qr"]["service"] = {"name": t["brand"], "category": t["category"], "verified": True}

    # signals used for explanation and confidence
    all_signals = list(msg_signals)
    for r in reports:
        all_signals.extend(r._signals)
    case.signals = dedupe(all_signals)

    checks = {"message_rules": "done"}
    tier = "NONE"
    if deciding is not None:
        checks.update(deciding.checks)
        tier = deciding.trust["tier"]
    elif case.kind == "qr":
        checks["qr_payload"] = "done"
    confidence, factors = V.confidence_for(verdict, case.signals, checks, tier)
    if any(s.id == "UPI_VALID" for s in case.signals):
        # the format is valid but the payee's real identity cannot be verified here
        confidence = min(confidence, 0.8)
    if not reports:
        # wording-only judgement (no link evidence) is never near-certain
        confidence = min(confidence, 0.8 if verdict == "SAFE" and not any(s.polarity == "trust" for s in case.signals) else 0.9)

    # score breakdown (risk contributions, largest first; trust shown as negatives)
    contrib: dict[str, int] = {}
    for s in case.signals:
        contrib[s.label] = contrib.get(s.label, 0) + (s.points if s.polarity == "risk" else -s.points)
    breakdown = [{"signal": k, "points": v} for k, v in sorted(contrib.items(), key=lambda kv: -abs(kv[1]))]

    assurance = None
    if verdict == "SAFE":
        tiers = {r.trust["tier"] for r in reports}
        verified = any(s.id in {"VERIFIED_SERVICE", "GENUINE_ALERT_PATTERN"} for s in case.signals) or (tiers and tiers <= {"OFFICIAL", "POPULAR"})
        assurance = "verified" if verified else "no_problems_found"

    dangerous_ids = ids | {s.id for r in reports for s in r._signals if s.polarity == "risk"}
    case.result = {
        "schema_version": 2,
        "verdict": verdict,
        "assurance": assurance,
        "risk_score": score if score is not None else 0,
        "risk_level": V.risk_level_for(verdict, score),
        "confidence": confidence,
        "confidence_factors": factors,
        "decision_path": path,
        "input_kind": case.kind,
        "urls": [r.to_dict() for r in reports],
        "skipped_urls": case.skipped_urls,
        "entities": case.msg.entities if case.msg else {},
        "message_signals": [s.to_dict() for s in msg_signals],
        "score_breakdown": breakdown,
        "evidence": [f"{s.label}: {s.explanation}" for s in sorted(case.signals, key=lambda s: -s.points)],
        "weights_version": WEIGHTS_VERSION,
        "risk_ids": sorted(dangerous_ids),
        "reasons": [],
        "recommendation": "",
        "reasoning_model": "",
        "analysis_note": "",
    }
    case.result.update(case.extra)
    return case


def investigate_sync(case: Case) -> Case:
    """Run extract -> message -> urls -> decide (no explanation step)."""
    for step in (step_extract, step_message, step_urls, step_decide):
        case = step(case)
    return case
