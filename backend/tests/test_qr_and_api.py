import io
from pathlib import Path

import pytest
import qrcode
from PIL import Image

from app.engine.analysis import investigate_sync
from app.qr.analyze import case_from_text
from app.qr.payload import classify
from app.services.qr import decode_all

SAMPLE = Path(__file__).parent / "sample_screenshot.png"
GPAY = "upi://pay?pa=store@okaxis&pn=Fresh%20Mart&mc=5411&cu=INR"


def qr_png(text: str, box_size: int = 8) -> bytes:
    img = qrcode.make(text, box_size=box_size, border=4)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def run(text):
    return investigate_sync(case_from_text(text)).result


# ---------------- payload classification ----------------
@pytest.mark.parametrize("text,kind", [
    (GPAY, "UPI"), ("https://open.spotify.com/track/xyz", "URL"), ("spotify:track:abc", "DEEPLINK"),
    ("WIFI:T:WPA;S:Cafe;P:pass;;", "WIFI"), ("javascript:alert(1)", "DANGEROUS"), ("sbi.co.in/login", "URL"),
    ("tel:+919876543210", "TEL"), ("bitcoin:1BoatSLRHtKNngkdXEeobR76b53LETtpyT", "CRYPTO"), ("just some words", "TEXT"),
])
def test_classify(text, kind):
    assert classify(text).kind == kind


def test_classifier_never_raises_on_junk():
    import random
    rng = random.Random(1)
    for _ in range(500):
        classify("".join(chr(rng.randint(1, 0x2fff)) for _ in range(rng.randint(0, 60))))


# ---------------- verdicts ----------------
def test_valid_upi_payment_qr_is_safe_and_shows_payee():
    r = run(GPAY)
    assert r["verdict"] == "SAFE"
    assert r["qr"]["summary"]["payee"] == "Fresh Mart" and r["qr"]["summary"]["vpa"] == "store@okaxis"
    assert r["confidence"] <= 0.8


def test_upi_with_unknown_bank_handle_is_flagged():
    assert run("upi://pay?pa=shop@fakebank99&pn=Shop")["verdict"] in {"SUSPICIOUS", "DANGEROUS"}


def test_upi_refund_desk_payee_is_flagged():
    assert run("upi://pay?pa=9812345678@ybl&pn=SBI%20Refund%20Dept&am=4999")["verdict"] == "DANGEROUS"


def test_spotify_qr_is_verified_safe():
    r = run("https://open.spotify.com/track/4uLU6hMCjMI75M1A2tKUQC")
    assert r["verdict"] == "SAFE" and r["qr"]["service"]["name"] == "Spotify"


def test_lookalike_spotify_is_dangerous():
    assert run("https://open.spotify.com.verify-login.top/track/1")["verdict"] == "DANGEROUS"


def test_phishing_url_qr_is_dangerous():
    assert run("http://sbi-kyc-update.top/login")["verdict"] == "DANGEROUS"


def test_javascript_qr_is_dangerous():
    assert run("javascript:alert(1)")["verdict"] == "DANGEROUS"


def test_same_url_same_verdict_as_text_and_qr():
    from app.engine.analysis import Case
    url = "https://hdfcbank-secure.in/login"
    text = investigate_sync(Case(url)).result
    assert text["verdict"] == run(url)["verdict"] and text["risk_score"] == run(url)["risk_score"]


# ---------------- decoder ----------------
def test_decoder_reads_generated_codes():
    assert decode_all(qr_png(GPAY))[0]["text"] == GPAY


def test_decoder_reads_small_and_rotated_codes():
    img = Image.open(io.BytesIO(qr_png("https://example.org/a", box_size=3))).rotate(90, expand=True)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    assert decode_all(buf.getvalue())[0]["text"] == "https://example.org/a"


def test_decoder_returns_nothing_for_photo_without_qr():
    assert decode_all(SAMPLE.read_bytes()) == []


# ---------------- API ----------------
def test_home_and_health(client):
    assert client.get("/").json()["project"] == "ScamShield"
    assert client.get("/health").json()["status"] == "ok"


def test_text_endpoint(client):
    body = client.post("/investigate", json={"message": "URGENT your SBI account is blocked, share OTP now", "claimed_organization": "SBI"}).json()
    assert body["verdict"] == "DANGEROUS" and body["schema_version"] == 2
    assert {"risk_score", "risk_level", "confidence", "reasons", "recommendation", "evidence", "score_breakdown", "reasoning_model"} <= body.keys()


def test_unknown_and_oversized_fields_rejected(client):
    assert client.post("/investigate", json={"message": "hi", "image_path": "C:/Windows/win.ini"}).status_code == 422
    assert client.post("/investigate", json={"message": "x" * 6000}).status_code == 422
    assert client.post("/investigate", json={}).status_code == 422


def test_qr_endpoint_reads_upload(client):
    r = client.post("/investigate/qr", files={"file": ("q.png", qr_png(GPAY), "image/png")})
    assert r.status_code == 200 and r.json()["verdict"] == "SAFE" and r.json()["decoded_text"] == GPAY


def test_qr_endpoint_multi_code_takes_worst(client):
    a = Image.open(io.BytesIO(qr_png(GPAY)))
    b = Image.open(io.BytesIO(qr_png("http://sbi-kyc-update.top/login")))
    canvas = Image.new("RGB", (a.width + b.width + 40, max(a.height, b.height) + 40), "white")
    canvas.paste(a, (20, 20))
    canvas.paste(b, (a.width + 20, 20))
    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    r = client.post("/investigate/qr", files={"file": ("q.png", buf.getvalue(), "image/png")}).json()
    assert r["verdict"] == "DANGEROUS" and len(r["qr_codes"]) == 2


def test_qr_endpoint_without_qr_is_422(client):
    r = client.post("/investigate/qr", files={"file": ("a.png", SAMPLE.read_bytes(), "image/png")})
    assert r.status_code == 422


def test_qr_text_endpoint(client):
    r = client.post("/investigate/qr-text", json={"text": "https://open.spotify.com/track/abc"})
    assert r.status_code == 200 and r.json()["verdict"] == "SAFE"


def test_upload_validation(client):
    assert client.post("/investigate/qr", files={"file": ("a.png", b"", "image/png")}).status_code == 400
    assert client.post("/investigate/qr", files={"file": ("a.png", b"MZ" + b"\x00" * 50, "image/png")}).status_code == 415
    assert client.post("/investigate/image", files={"file": ("a.txt", b"hello world", "text/plain")}).status_code == 415


def test_image_endpoint_unreadable_image_is_422(client):
    blank = io.BytesIO()
    Image.new("RGB", (300, 300), "white").save(blank, format="PNG")
    r = client.post("/investigate/image", files={"file": ("a.png", blank.getvalue(), "image/png")})
    assert r.status_code in {422, 503}


def test_stream_endpoint_order(client):
    with client.stream("POST", "/investigate/stream", json={"message": "send your otp now or account blocked https://hdfcbank-secure.in"}) as resp:
        text = "".join(resp.iter_text())
    events = [line.split(": ", 1)[1] for line in text.splitlines() if line.startswith("event: ")]
    assert events[0] == "stage" and "verdict" in events and events[-1] == "done"
    assert events.index("verdict") < events.index("explanation") < events.index("done")


def test_stream_reports_errors_as_events(client):
    with client.stream("POST", "/investigate/qr/stream", files={"file": ("a.png", SAMPLE.read_bytes(), "image/png")}) as resp:
        text = "".join(resp.iter_text())
    assert "event: error" in text
