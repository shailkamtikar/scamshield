import io

import httpx
import qrcode
import respx

from app.api import middleware
from app.config import settings
from app.engine.analysis import Case, investigate_sync
from app.engine.signals import make
from app.engine.verdict import assess_url
from app.intel import page, sandbox, url_model
from app.intel.urls import parse_url
from PIL import Image


def run(text):
    return investigate_sync(Case(text)).result


def ids(r):
    return {s["id"] for s in r["message_signals"]}


# ---------------- page inspection, calibrated on real pages ----------------
def test_ordinary_login_form_is_not_treated_as_phishing():
    html = "<title>Hockey Wilderness</title><form><input type=password name=pw></form><p>News</p>"
    report = page.analyze(parse_url("https://hockeywilderness.com/"), html)
    assert {s.id for s in report} == {"LOGIN_FORM_UNTRUSTED"}
    assert assess_url(report, "UNKNOWN", "OK").verdict == "SAFE"


def test_brand_in_page_body_alone_is_not_impersonation():
    html = "<title>Rahul's blog</title><p>I paid with Paytm and SBI at the login counter</p>"
    assert page.analyze(parse_url("https://rahulblog.in/"), html) == []


def test_hosting_provider_phishing_warning_is_decisive():
    html = "<title>Suspected Phishing | Cloudflare</title><form></form>"
    report = page.analyze(parse_url("https://abc.pages.dev/"), html)
    assert [s.id for s in report] == ["HOST_FLAGGED_PAGE"]
    assert assess_url(report, "UNKNOWN", "OK").verdict == "DANGEROUS"


# ---------------- real-browser sandbox (urlscan) ----------------
SEARCH_HIT = {"results": [{
    "_id": "abc", "task": {"uuid": "abc", "time": "2026-10-01T00:00:00Z"},
    "page": {"url": "https://final.example/", "title": "Login", "apexDomainAgeDays": 3, "tlsAgeDays": 0},
    "screenshot": "https://urlscan.io/screenshots/abc.png",
}]}


@respx.mock
def test_sandbox_uses_earlier_scan_without_key():
    sandbox._cache.clear()
    respx.get("https://urlscan.io/api/v1/search/").mock(return_value=httpx.Response(200, json=SEARCH_HIT))
    parsed = parse_url("https://some-site.example.com/")
    result = sandbox.scan(parsed)
    assert result.status == "done" and result.source == "earlier_scan" and result.screenshot.endswith("abc.png")
    assert {s.id for s in sandbox.to_signals(parsed, result, have_age=False)} == {"DOMAIN_AGE_LT_30D"}


@respx.mock
def test_sandbox_live_scan_is_unlisted_and_reads_verdict(monkeypatch):
    sandbox._cache.clear()
    monkeypatch.setattr(settings, "urlscan_api_key", "k")
    monkeypatch.setattr(sandbox, "FIRST_POLL_DELAY", 0.0)
    submit = respx.post("https://urlscan.io/api/v1/scan/").mock(return_value=httpx.Response(200, json={"uuid": "u1"}))
    respx.get("https://urlscan.io/api/v1/result/u1/").mock(side_effect=[
        httpx.Response(404),
        httpx.Response(200, json={"task": {}, "page": {"url": "https://x.example/"}, "verdicts": {"overall": {"malicious": True, "score": 100, "brands": ["SBI"]}}}),
    ])
    monkeypatch.setattr(sandbox.time, "sleep", lambda s: None)
    parsed = parse_url("https://another-site.example.com/")
    result = sandbox.scan(parsed, budget=5)
    assert b'"unlisted"' in submit.calls[0].request.content
    assert result.malicious is True and result.source == "live_scan"
    signals = sandbox.to_signals(parsed, result, have_age=True)
    assert signals[0].id == "SANDBOX_MALICIOUS" and assess_url(signals, "UNKNOWN", "OK").verdict == "DANGEROUS"


@respx.mock
def test_sandbox_clean_result_and_outage_fail_soft(monkeypatch):
    sandbox._cache.clear()
    respx.get("https://urlscan.io/api/v1/search/").mock(return_value=httpx.Response(500))
    assert sandbox.scan(parse_url("https://third-site.example.com/")).status == "unavailable"


# ---------------- learned model ----------------
def test_model_loads_and_only_scores_names():
    assert url_model.score("sbi.co.in") is not None
    assert isinstance(url_model.is_risky("mycoolbakery.in"), bool)


def test_model_signal_alone_cannot_make_a_link_dangerous():
    a = assess_url([make("ML_DOMAIN_RISK", "x", "t", "k")], "UNKNOWN", "OK")
    assert a.verdict == "SUSPICIOUS"


# ---------------- Hindi ----------------
def test_devanagari_scam_is_detected():
    r = run("आपका खाता बंद हो जाएगा। तुरंत अपना ओटीपी भेजें और केवाईसी अपडेट करें")
    assert {"CREDENTIAL_REQUEST", "FEAR_OR_THREAT"} <= ids(r) and r["verdict"] == "DANGEROUS"


def test_devanagari_advisory_is_not_a_credential_request():
    assert "CREDENTIAL_REQUEST" not in ids(run("अपना ओटीपी किसी को न बताएं"))


# ---------------- assurance ----------------
def test_verified_and_unknown_safe_are_different_claims():
    assert run("https://www.sbi.co.in/")["assurance"] == "verified"
    assert run("have a look at https://mycoolbakery.in")["assurance"] == "no_problems_found"
    assert run("hello, lunch tomorrow?")["assurance"] == "no_links"
    assert run("http://sbi-kyc-update.top/login")["assurance"] is None


# ---------------- multi-QR through the stream ----------------
def test_stream_reports_the_worst_of_several_codes(client):
    a = qrcode.make("upi://pay?pa=store@okaxis&pn=Fresh%20Mart", box_size=8)
    b = qrcode.make("http://sbi-kyc-update.top/login", box_size=8)
    canvas = Image.new("RGB", (a.size[0] + b.size[0] + 40, max(a.size[1], b.size[1]) + 40), "white")
    canvas.paste(a.get_image() if hasattr(a, "get_image") else a, (20, 20))
    canvas.paste(b.get_image() if hasattr(b, "get_image") else b, (a.size[0] + 20, 20))
    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    with client.stream("POST", "/investigate/qr/stream", files={"file": ("q.png", buf.getvalue(), "image/png")}) as resp:
        text = "".join(resp.iter_text())
    assert '"verdict": "DANGEROUS"' in text and '"qr_codes"' in text


# ---------------- public-endpoint protection ----------------
def test_rate_limit_returns_429_with_retry_after(client, monkeypatch):
    monkeypatch.setattr(settings, "rate_limit_per_minute", 2)
    monkeypatch.setattr(middleware, "limiter", middleware.RateLimiter())
    body = {"message": "hello"}
    assert client.post("/investigate", json=body).status_code == 200
    assert client.post("/investigate", json=body).status_code == 200
    third = client.post("/investigate", json=body)
    assert third.status_code == 429 and "retry-after" in third.headers
    assert client.get("/health").status_code == 200  # health is never limited


def test_access_key(client, monkeypatch):
    monkeypatch.setattr(settings, "api_access_key", "secret")
    assert client.post("/investigate", json={"message": "x"}).status_code == 401
    assert client.post("/investigate", json={"message": "x"}, headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.post("/investigate", json={"message": "x"}, headers={"X-API-Key": "secret"}).status_code == 200


def test_security_headers_and_request_id(client):
    r = client.get("/health")
    assert r.headers["x-content-type-options"] == "nosniff" and r.headers["x-request-id"]


def test_message_text_is_never_logged(client, caplog):
    import logging

    with caplog.at_level(logging.INFO, logger="scamshield"):
        client.post("/investigate", json={"message": "my secret otp is 998877"})
    assert "998877" not in caplog.text
