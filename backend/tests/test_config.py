from app.config import Settings


def test_boots_with_no_keys(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    assert Settings(_env_file=None).gemini_api_key is None


def test_cors_origins_from_comma_list(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "http://a.test, https://b.test")
    assert Settings(_env_file=None).cors_origins == ["http://a.test", "https://b.test"]


def test_gemini_unavailable_gives_rules_only(monkeypatch):
    from app.graph.graph import graph
    from app.graph.state import ScamShieldState
    from app.services.gemini import GeminiUnavailable

    def boom(*args, **kwargs):
        raise GeminiUnavailable("no key")

    monkeypatch.setattr("app.graph.nodes.gemini_reasoning.analyze_scam_evidence", boom)
    result = graph.invoke(ScamShieldState(message="URGENT send your OTP now"))
    assert result["reasoning_model"] == ""
    assert result["reasons"] and result["recommendation"]
