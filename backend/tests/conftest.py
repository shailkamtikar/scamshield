import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.gemini_schema import GeminiAssessment


@pytest.fixture(autouse=True)
def mock_gemini(monkeypatch):
    """Never call the real Gemini API in the normal test suite."""

    def fake_analyze(evidence, risk_score, score_breakdown):
        return (
            GeminiAssessment(
                risk_level="HIGH",
                confidence=0.8,
                reasons=["mocked reason"],
                recommendation="mocked recommendation",
            ),
            "mock-model",
        )

    monkeypatch.setattr(
        "app.graph.nodes.gemini_reasoning.analyze_scam_evidence", fake_analyze
    )


@pytest.fixture
def client():
    return TestClient(app)
