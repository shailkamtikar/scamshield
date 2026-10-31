from app.graph.state import ScamShieldState
from app.services.gemini import GeminiUnavailable, analyze_scam_evidence


def gemini_reasoning_node(state: ScamShieldState) -> ScamShieldState:
    """
    Use Gemini to reason over the evidence AND the already-computed
    deterministic risk_score/score_breakdown (risk_assessment_node runs
    before this one), producing confidence/reasons/recommendation.

    Gemini does NOT set risk_level or risk_score — those are deterministic
    and authoritative. Gemini's job is to explain them in plain language
    and give a confidence grounded in how much/strong the evidence is.

    When there is no evidence at all (e.g. a QR code or bare URL that
    triggered none of the deterministic checks), there is nothing for
    Gemini to reason about, so the call is skipped — but every field this
    node is responsible for is still explicitly assigned. Leaving them at
    their class defaults here previously caused `reasoning_model` to be
    dropped entirely from the graph's output (see state.py), producing a
    KeyError on the QR path, which hits this empty-evidence branch far
    more often than text/image since a decoded QR is usually just a bare
    URL with no surrounding social-engineering language.
    """

    if not state.evidence:
        state.confidence = 0.0
        state.reasons = []
        state.recommendation = (
            "No risk indicators were found in the provided content."
        )
        state.reasoning_model = ""
        return state

    try:
        assessment, model_used = analyze_scam_evidence(
            state.evidence,
            risk_score=state.risk_score,
            score_breakdown=state.score_breakdown,
        )
    except GeminiUnavailable:
        return _rules_only_result(state)

    state.confidence = assessment.confidence
    state.reasons = assessment.reasons
    state.recommendation = assessment.recommendation
    state.reasoning_model = model_used

    return state


_RULES_ONLY_RECOMMENDATIONS = {
    "CRITICAL": "Do not open any links, reply, or share any details. Delete the message and report it at cybercrime.gov.in or call 1930.",
    "HIGH": "Treat this as a likely scam. Do not click links or share details; verify through the organization's official website or app.",
    "MEDIUM": "Be cautious. Verify the sender through an official channel before acting.",
    "LOW": "No risk indicators were found, but never share OTPs or PINs with anyone.",
}


def _rules_only_result(state: ScamShieldState) -> ScamShieldState:
    """Deterministic explanation used when no Gemini key is configured."""

    state.reasons = [
        f"{item['signal']} (+{item['points']} points)"
        for item in state.score_breakdown
    ] or list(state.evidence[:5])
    state.recommendation = _RULES_ONLY_RECOMMENDATIONS.get(
        state.risk_level, _RULES_ONLY_RECOMMENDATIONS["MEDIUM"]
    )
    state.confidence = 0.5
    state.reasoning_model = ""
    return state
