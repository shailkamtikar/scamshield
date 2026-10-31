from pydantic import BaseModel, ConfigDict, Field


class InvestigationRequest(BaseModel):
    # Reject unknown fields so clients cannot smuggle in extra inputs.
    model_config = ConfigDict(extra="forbid")

    message: str = Field(
        ...,
        description="The suspicious message or text submitted by the user."
    )

    source: str = Field(
        default="web",
        description="Where the content came from (web, telegram, email, etc.)."
    )

    claimed_organization: str | None = Field(
        default=None,
        description="Organization claimed by the suspicious message."
    )
