from pydantic import BaseModel, Field


class GeminiAnalysis(BaseModel):
    """Explanation + a second opinion. Never a score, verdict or confidence."""

    is_scam_likely: bool = Field(description="True only if the message itself reads like a scam or phishing attempt.")
    scam_type: str = Field(description="Short label such as 'KYC phishing', 'fake courier fee', 'UPI collect scam', or 'none'.")
    reasons: list[str] = Field(description="2-5 plain-language reasons, each about ONE specific piece of evidence given.")
    recommendation: str = Field(description="One practical safety recommendation consistent with the verdict.")
