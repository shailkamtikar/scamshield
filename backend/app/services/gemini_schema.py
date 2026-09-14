from pydantic import BaseModel, Field


class GeminiAssessment(BaseModel):
    risk_level: str = Field(
        description="Risk level: LOW, MEDIUM, HIGH, or CRITICAL."
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in the assessment from 0 to 1."
    )

    reasons: list[str] = Field(
        description="Evidence-based reasons supporting the assessment."
    )

    recommendation: str = Field(
        description="Recommended safe action for the user."
    )