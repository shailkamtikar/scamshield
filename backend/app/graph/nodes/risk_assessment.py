from app.graph.state import ScamShieldState
from app.graph.signals import CATEGORY_LABELS, deduplicate_signals, derive_risk_level


def risk_assessment_node(state: ScamShieldState) -> ScamShieldState:
    """
    Calculate the deterministic numerical risk score AND the deterministic
    risk level from the structured signals collected by the investigation
    nodes (url_investigation, identity_verification, social_engineering).

    This is the single source of truth for risk_score and risk_level.
    Gemini (which runs after this node) reasons over the result to produce
    confidence/reasons/recommendation, but never sets or overrides these
    two fields — so they can never contradict each other, and the same
    normalized evidence always produces the same score regardless of
    whether it arrived as text, an OCR'd screenshot, or a decoded QR code.
    """

    deduplicated = deduplicate_signals(state.signals)

    total_score = sum(signal.points for signal in deduplicated)
    state.risk_score = min(total_score, 100)
    state.risk_level = derive_risk_level(state.risk_score)

    # Human-readable breakdown for the API response / UI / PDF, sorted by
    # contribution so the largest factors show first.
    breakdown_by_category: dict[str, int] = {}
    for signal in deduplicated:
        label = CATEGORY_LABELS.get(signal.category, signal.category)
        breakdown_by_category[label] = breakdown_by_category.get(label, 0) + signal.points

    state.score_breakdown = [
        {"signal": label, "points": points}
        for label, points in sorted(breakdown_by_category.items(), key=lambda item: -item[1])
    ]

    return state
