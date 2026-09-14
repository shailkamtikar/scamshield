from app.graph.graph import graph
from app.graph.state import ScamShieldState


def run_investigation(state: ScamShieldState) -> dict:
    """
    Run the ScamShield LangGraph investigation pipeline and shape the
    response returned by every entry point (SMS/text, SMS image, QR code).
    """

    result = graph.invoke(state)

    return {
        "risk_score": result["risk_score"],
        "risk_level": result["risk_level"],
        "confidence": result["confidence"],
        "reasons": result["reasons"],
        "recommendation": result["recommendation"],
        "evidence": result["evidence"],
        "score_breakdown": result["score_breakdown"],
        "reasoning_model": result["reasoning_model"],
    }
