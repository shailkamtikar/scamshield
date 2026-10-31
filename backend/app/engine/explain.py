"""
Explanation step. Gemini (when available) writes the plain-language reasons
and recommendation and gives a second opinion on the message wording; a
deterministic template is used when it is not. Gemini can only RAISE a SAFE
verdict to SUSPICIOUS; it can never lower a verdict, set a score, or set the
confidence.
"""

import re

from app.engine import classify
from app.engine import verdict as V
from app.engine.analysis import Case
from app.engine.signals import make
from app.services import gemini

RECOMMENDATIONS = {
    "SAFE": "No threats were found. Even so, never share OTPs, PINs or passwords, and open official apps or websites by typing the address yourself.",
    "SUSPICIOUS": "Do not click links or share any details yet. Check with the organisation through its official website, app or helpline before acting.",
    "DANGEROUS": "Do not open the link, reply, call the number or share any code. Delete the message and report it at cybercrime.gov.in or call 1930. If you already lost money, call 1930 immediately.",
    "COULD_NOT_VERIFY": "This link does not exist or could not be reached, so it could not be checked. Do not rely on it; ask the sender or use the organisation's official channel.",
}


# Official domains, but anyone can create a link on them, so the domain says nothing about who sent it.
from app.intel.trust import OPEN_LINK_SERVICES  # noqa: E402

PROMO_ADVICE = {
    "promotion": "This reads like an advertisement and the link goes to the organisation's own site. Reading it is harmless; offers can still end, so check the details in the official app or website.",
    "spam": "This reads like an unwanted advertisement. Reading it is harmless, but we could not tie it to a known organisation or confirm where its link leads. Don't tap it; delete it, or open the organisation's official app or website yourself.",
    "promotion_unverified": "This reads like an advertisement. Reading it is harmless, but we could not confirm where its link leads. Don't tap it; open the organisation's official app or website yourself instead.",
}

PAYMENT_ADVICE = "Check that the name shown is who you mean to pay before you confirm. Remember that you never need to scan a QR or enter your PIN to receive money."


def template_reasons(case: Case) -> list[str]:
    result = case.result
    risk = sorted((s for s in case.signals if s.polarity == "risk"), key=lambda s: -s.points)
    trust = [s for s in case.signals if s.polarity == "trust"]
    reasons = [s.explanation for s in risk[:5]]
    if not reasons and trust:
        reasons = [s.explanation for s in trust[:3]]
    if not reasons:
        if result["verdict"] == "COULD_NOT_VERIFY" and case.url_reports:
            r = case.url_reports[0].reachability or {}
            reasons = [f"The link could not be reached ({r.get('detail') or r.get('outcome', 'no response')})."]
        else:
            reasons = ["No scam wording, suspicious links or other risk indicators were found."]
    return reasons


def _mentions_own_official_address(case: Case) -> bool:
    """The text names an organisation AND contains that organisation's real e-mail or web address."""
    from app.intel.trust import official_index

    text = case.message.lower()
    brands = {b.name for b in (case.msg.mentioned_brands if case.msg else [])}
    index = official_index()
    for domain, brand in index.items():
        if brand.name in brands and re.search(rf"[@/.]{re.escape(domain)}\b", text):
            return True
    return False


def explain(case: Case, use_llm: bool = True) -> Case:
    result = case.result
    verdict = result["verdict"]
    result["reasons"] = template_reasons(case)
    fixed_advice = PAYMENT_ADVICE if result.get("assurance") == "valid_payment" else PROMO_ADVICE.get(result.get("assurance") or "")
    result["recommendation"] = fixed_advice or RECOMMENDATIONS[verdict]
    result["reasoning_model"] = ""

    if not use_llm or (not case.signals and not case.message.strip()):
        return case

    summary = {
        "verdict": verdict,
        "score": result["risk_score"],
        "text": case.message[:1500],
        "signals": [f"{s.label}: {s.explanation}" for s in sorted(case.signals, key=lambda s: -s.points)[:12]],
        "urls": [f"{u['url']} -> {u['verdict']} ({u['trust']['tier']})" for u in result["urls"]],
    }
    try:
        analysis, model = gemini.analyze(summary)
    except gemini.GeminiUnavailable as err:
        result["analysis_note"] = "Explanation written by built-in rules (AI explanation unavailable)."
        return case

    cleaned = [r.strip() for r in analysis.reasons if r and r.strip()][:5]
    if cleaned:
        result["reasons"] = cleaned
    result["recommendation"] = fixed_advice or analysis.recommendation.strip() or RECOMMENDATIONS[verdict]
    result["reasoning_model"] = model
    result["scam_type"] = analysis.scam_type

    # Second opinion: may raise SAFE -> SUSPICIOUS, never anything else.
    # Rules only know wording they were written for; this is what catches new
    # scam scripts. A verified official link is not overruled by an AI opinion.
    quote = " ".join(analysis.evidence_quote.lower().split())
    quoted = bool(quote) and quote in " ".join(case.message.lower().split())
    unknown_links = any(u["trust"]["tier"] == "UNKNOWN" for u in result["urls"])
    concrete = analysis.asks_for in {"secret_code_or_password", "money", "personal_details", "install_app"} or (
        analysis.asks_for in {"click_link", "call_number"} and unknown_links
    )
    if result.get("assurance") in PROMO_ADVICE:
        # an ad always says "apply", "pay" or "click"; only a request for a secret or an install is a scam signal
        concrete = analysis.asks_for in {"secret_code_or_password", "install_app"}
    names_own_official_address = _mentions_own_official_address(case)
    all_verified = bool(result["urls"]) and all(u["trust"]["tier"] == "OFFICIAL" and u["registrable"] not in OPEN_LINK_SERVICES for u in result["urls"])
    genuine = any(s.id == "GENUINE_ALERT_PATTERN" for s in case.signals)
    if verdict == "SAFE" and analysis.is_scam_likely and concrete and quoted and not all_verified and not genuine and not (names_own_official_address and not unknown_links):
        sig = make("LLM_SCAM_INTENT", f"AI review of the wording: looks like {analysis.scam_type}.", "gemini")
        case.signals.append(sig)
        result["verdict"] = "SUSPICIOUS"
        result["risk_score"] = max(result["risk_score"], 30)
        result["risk_level"] = V.risk_level_for("SUSPICIOUS", result["risk_score"])
        result["assurance"] = None
        classify.apply(result)
        result["confidence"] = min(result["confidence"], 0.7)
        result["decision_path"].append("L1_LLM_SECOND_OPINION")
        result["evidence"].insert(0, f"{sig.label}: {sig.explanation}")
        result["recommendation"] = RECOMMENDATIONS["SUSPICIOUS"]
    return case
