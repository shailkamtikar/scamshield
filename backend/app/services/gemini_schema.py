from typing import Literal

from pydantic import BaseModel, Field


class GeminiAnalysis(BaseModel):
    """Explanation + a second opinion. Never a score, verdict or confidence."""

    is_scam_likely: bool = Field(description="True only if the message itself reads like a scam or phishing attempt.")
    scam_type: str = Field(description="Short label such as 'KYC phishing', 'fake courier fee', 'UPI collect scam', or 'none'.")
    asks_for: Literal["none", "secret_code_or_password", "money", "personal_details", "install_app", "call_number", "click_link"] = Field(
        description="The single most concerning thing the message asks the reader to do, or 'none'."
    )
    evidence_quote: str = Field(description="The exact words copied from the message that make the request concerning, or an empty string.")
    reasons: list[str] = Field(description="2-5 plain-language reasons, each about ONE specific piece of evidence given.")
    recommendation: str = Field(description="One practical safety recommendation consistent with the verdict.")
