from pydantic import BaseModel, Field

from app.graph.signals import RiskSignal


class ScamShieldState(BaseModel):
    message: str

    source: str = "web"

    claimed_organization: str | None = None

    image_path: str | None = None

    urls: list[str] = Field(default_factory=list)

    emails: list[str] = Field(default_factory=list)

    phone_numbers: list[str] = Field(default_factory=list)

    evidence: list[str] = Field(default_factory=list)

    # Structured, deduplicated, deterministic evidence — the source of
    # truth risk_assessment_node scores from. evidence[] above stays as
    # the human-readable trail shown in the UI and given to Gemini.
    signals: list[RiskSignal] = Field(default_factory=list)

    score_breakdown: list[dict] = Field(default_factory=list)

    risk_score: int = 0

    risk_level: str = "LOW"

    confidence: float = 0.0

    reasons: list[str] = Field(default_factory=list)

    recommendation: str = ""

    # NOT Optional: LangGraph's pydantic-schema channel seeding drops a
    # field entirely from graph.invoke()'s output dict if it is left at a
    # `None` default and no node ever assigns it (as opposed to fields with
    # a concrete default like "" or [], which always survive). A `str|None`
    # default here caused exactly that for QR investigations whose decoded
    # text produced no evidence (see gemini_reasoning_node).
    reasoning_model: str = ""