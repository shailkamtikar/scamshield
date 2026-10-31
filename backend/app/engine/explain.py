"""
Explanation step. Gemini (when available) writes the plain-language reasons
and recommendation and gives a second opinion on the message wording; a
deterministic template is used when it is not. Gemini can only RAISE a SAFE
verdict to SUSPICIOUS; it can never lower a verdict, set a score, or set the
confidence.
"""

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


def explain(case: Case, use_llm: bool = True) -> Case:
    result = case.result
    verdict = result["verdict"]
    result["reasons"] = template_reasons(case)
    result["recommendation"] = RECOMMENDATIONS[verdict]
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
    result["recommendation"] = analysis.recommendation.strip() or RECOMMENDATIONS[verdict]
    result["reasoning_model"] = model
    result["scam_type"] = analysis.scam_type

    # Second opinion: may raise SAFE -> SUSPICIOUS, never anything else.
    has_some_risk = any(s.polarity == "risk" for s in case.signals) or any(u["trust"]["tier"] == "UNKNOWN" for u in result["urls"])
    if verdict == "SAFE" and analysis.is_scam_likely and has_some_risk:
        sig = make("LLM_SCAM_INTENT", f"AI review of the wording: looks like {analysis.scam_type}.", "gemini")
        case.signals.append(sig)
        result["verdict"] = "SUSPICIOUS"
        result["risk_score"] = max(result["risk_score"], 30)
        result["risk_level"] = V.risk_level_for("SUSPICIOUS", result["risk_score"])
        result["confidence"] = min(result["confidence"], 0.7)
        result["decision_path"].append("L1_LLM_SECOND_OPINION")
        result["evidence"].insert(0, f"{sig.label}: {sig.explanation}")
        result["recommendation"] = RECOMMENDATIONS["SUSPICIOUS"]
    return case
