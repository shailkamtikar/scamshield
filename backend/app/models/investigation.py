from pydantic import BaseModel, Field


class InvestigationRequest(BaseModel):
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

    image_path: str | None = Field(
        default=None,
        description="Path to an uploaded screenshot for OCR analysis."
    )