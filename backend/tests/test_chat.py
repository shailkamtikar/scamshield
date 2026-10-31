import json

from app.api import chat as chat_api
from app.config import settings


def body(text="how do I spot a fake KYC message?", **extra):
    return {"messages": [{"role": "user", "text": text}], **extra}


def test_chat_is_off_without_its_own_key(client, monkeypatch):
    monkeypatch.setattr(settings, "gemini_chat_api_key", None)
    assert client.post("/chat", json=body()).status_code == 503
    assert client.get("/health").json()["providers"]["chat"] is False


def test_chat_never_uses_the_checker_key(client, monkeypatch):
    monkeypatch.setattr(settings, "gemini_api_key", "checker-key")
    monkeypatch.setattr(settings, "gemini_chat_api_key", None)
    assert client.post("/chat", json=body()).status_code == 503


def test_chat_validation(client, monkeypatch):
    monkeypatch.setattr(settings, "gemini_chat_api_key", "k")
    assert client.post("/chat", json={"messages": []}).status_code == 422
    assert client.post("/chat", json=body("x" * 1300)).status_code == 422
    assert client.post("/chat", json=body(context="y" * 2100)).status_code == 422
    assert client.post("/chat", json={"messages": [{"role": "system", "text": "hi"}]}).status_code == 422
    assert client.post("/chat", json={"messages": [{"role": "assistant", "text": "hi"}]}).status_code == 422
    assert client.post("/chat", json={**body(), "extra": 1}).status_code == 422
    assert client.post("/chat", json={"messages": [{"role": "user", "text": "a"}] * 13}).status_code == 422


def test_chat_streams_and_includes_result_context(client, monkeypatch):
    monkeypatch.setattr(settings, "gemini_chat_api_key", "k")
    seen = {}

    class Chunk:
        def __init__(self, t):
            self.text = t

    class FakeModels:
        def generate_content_stream(self, model, contents, config):
            seen["system"] = config.system_instruction
            seen["roles"] = [c.role for c in contents]
            return iter([Chunk("Call "), Chunk("1930.")])

    class FakeClient:
        models = FakeModels()

    monkeypatch.setattr(chat_api, "_get_client", lambda: FakeClient())
    with client.stream("POST", "/chat", json=body(context="Verdict: DANGEROUS")) as r:
        text = "".join(r.iter_text())
    pieces = [json.loads(l[6:])["t"] for l in text.splitlines() if l.startswith("data: ") and '"t"' in l]
    assert "".join(pieces) == "Call 1930." and "event: done" in text
    assert "Verdict: DANGEROUS" in seen["system"] and seen["roles"] == ["user"]


def test_chat_failure_is_a_clean_event(client, monkeypatch):
    monkeypatch.setattr(settings, "gemini_chat_api_key", "k")

    class Boom:
        class models:
            @staticmethod
            def generate_content_stream(**kwargs):
                raise RuntimeError("quota")

    monkeypatch.setattr(chat_api, "_get_client", lambda: Boom())
    with client.stream("POST", "/chat", json=body()) as r:
        text = "".join(r.iter_text())
    assert "event: error" in text and "quota" not in text


def test_chat_is_rate_limited_like_the_checker(client, monkeypatch):
    from app.api import middleware

    monkeypatch.setattr(settings, "gemini_chat_api_key", None)
    monkeypatch.setattr(settings, "rate_limit_per_minute", 1)
    monkeypatch.setattr(middleware, "limiter", middleware.RateLimiter())
    client.post("/chat", json=body())
    assert client.post("/chat", json=body()).status_code == 429
