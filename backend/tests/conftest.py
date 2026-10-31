import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.services import gemini, vision


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    """Normal test runs never touch the network, Gemini or any API."""
    monkeypatch.setattr(settings, "enable_network_intel", False)
    monkeypatch.setattr(settings, "enable_vision", False)
    monkeypatch.setattr(settings, "rate_limit_per_minute", 100000)
    monkeypatch.setattr(settings, "rate_limit_per_day", 100000)
    monkeypatch.setattr(settings, "urlscan_api_key", None)

    def no_gemini(summary):
        raise gemini.GeminiUnavailable("tests run without Gemini")

    monkeypatch.setattr(gemini, "analyze", no_gemini)
    monkeypatch.setattr(vision, "read_image", lambda data, mime: None)


@pytest.fixture
def client():
    return TestClient(app)
