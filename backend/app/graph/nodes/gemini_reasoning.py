from app.graph.state import ScamShieldState
from app.services.gemini import analyze_scam_evidence


def gemini_reasoning_node(state: ScamShieldState) -> ScamShieldState:
    """
    Use Gemini to reason over the evidence AND the already-computed
    deterministic risk_score/score_breakdown (risk_assessment_node runs
    before this one), producing confidence/reasons/recommendation.

    Gemini does NOT set risk_level or risk_score — those are deterministic
    and authoritative. Gemini's job is to explain them in plain language
    and give a confidence grounded in how much/strong the evidence is.
    """

    if not state.evidence:
        return state

    assessment, model_used = analyze_scam_evidence(
        state.evidence,
        risk_score=state.risk_score,
        score_breakdown=state.score_breakdown,
    )

    state.confidence = assessment.confidence
    state.reasons = assessment.reasons
    state.recommendation = assessment.recommendation
    state.reasoning_model = model_used

    return state
