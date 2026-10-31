from pydantic import BaseModel, ConfigDict, Field


class InvestigationRequest(BaseModel):
    # Reject unknown fields so clients cannot smuggle in extra inputs.
    model_config = ConfigDict(extra="forbid")

    message: str = Field(..., min_length=1, max_length=5000, description="The suspicious message or text.")
    source: str = Field(default="web", max_length=40, description="Where the content came from.")
    claimed_organization: str | None = Field(default=None, max_length=80, description="Organization the message claims to be from.")


class QrTextRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., min_length=1, max_length=4000, description="Decoded QR content.")
    claimed_organization: str | None = Field(default=None, max_length=80)
