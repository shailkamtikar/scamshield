import shutil
from pathlib import Path

from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


_WINDOWS_TESSERACT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")


def _default_tesseract() -> str | None:
    found = shutil.which("tesseract")
    if found:
        return found
    if _WINDOWS_TESSERACT.exists():
        return str(_WINDOWS_TESSERACT)
    return None


class Settings(BaseSettings):
    """
    Single source of configuration, read from environment variables / .env.
    Every external key is optional: the engine degrades gracefully when a
    provider is not configured instead of failing at import time.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    gemini_api_key: str | None = None
    primary_gemini_model: str = "gemini-3.6-flash"
    secondary_gemini_model: str = "gemini-3.5-flash-lite"

    # The lighter model answers in ~1s versus 5-40s, so it goes first by default.
    gemini_fast_first: bool = True
    gemini_timeout_seconds: int = 10

    tesseract_cmd: str | None = Field(default_factory=_default_tesseract)

    cors_origins: Annotated[list[str], NoDecode] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Reserved for later phases (threat-intel providers, access control).
    safe_browsing_api_key: str | None = None
    virustotal_api_key: str | None = None
    urlhaus_auth_key: str | None = None
    urlscan_api_key: str | None = None
    api_access_key: str | None = None

    # Feature switches (all default on).
    enable_network_intel: bool = True
    enable_page_inspection: bool = True
    enable_fetch: bool = True  # connect to links to follow redirects / check they exist
    enable_vision: bool = True
    enable_sandbox: bool = True
    sandbox_budget_seconds: int = 20

    # Public-endpoint protection
    rate_limit_per_minute: int = 20
    rate_limit_per_day: int = 300
    trust_proxy_headers: bool = False  # set true behind Render's proxy

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value):
        if isinstance(value, str) and not value.lstrip().startswith("["):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("tesseract_cmd", "gemini_api_key", mode="before")
    @classmethod
    def _blank_to_none(cls, value):
        return value or None

    def configured_providers(self) -> dict[str, bool]:
        return {
            "gemini": bool(self.gemini_api_key),
            "safe_browsing": bool(self.safe_browsing_api_key),
            "virustotal": bool(self.virustotal_api_key),
            "urlhaus": bool(self.urlhaus_auth_key),
            "sandbox_live_scan": bool(self.urlscan_api_key),
            "tesseract": bool(self.tesseract_cmd),
        }


settings = Settings()
