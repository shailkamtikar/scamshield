"""
Cross-modal consistency test for ScamShield's deterministic risk engine.

Verifies that the SAME underlying URL/brand evidence produces the SAME
deterministic risk contribution regardless of whether ScamShield receives
it as typed text, an OCR'd screenshot, or a decoded QR code — and that a
legitimate domain is not penalized just because of how it was submitted.

Uses only synthetic, safe test domains (never live/real malicious
infrastructure). Exercises the REAL services: the real OCR engine
(services/ocr.py) reads a real generated image, and the real QR decoder
(services/qr.py) reads a real generated QR code — this is not simulated.
"""

import tempfile
from pathlib import Path

import cv2
from PIL import Image, ImageDraw, ImageFont

from app.graph.graph import graph
from app.graph.signals import derive_risk_level
from app.graph.state import ScamShieldState
from app.services.ocr import extract_text_from_image
from app.services.qr import decode_qr_code


PHISHING_URL = "https://miconsoft-login.com"
LEGITIMATE_URL = "https://www.microsoft.com/"
NETFLIX_LOOKALIKE_URL = "https://netfl1x-billing-update.com"
BARE_URL = "https://secure-login-update.info"
# A combosquat-shaped domain with NO claimed organization — the exact
# real-world QR scenario: identity_verification_node cannot compare
# against a brand it was never told, so this URL must rely entirely on
# the brand-agnostic structural signal to avoid scoring zero.
NO_CLAIM_COMBOSQUAT_URL = "https://netflix-billing-support.example"

URL_SIGNAL_LABELS = {
    "Possible brand impersonation",
    "Suspicious URL keyword",
    "Insecure (non-HTTPS) URL",
    "URL uses a raw IP address",
    "Excessive subdomains",
    "Lookalike domain compound structure",
}


def run(label, message, claimed_organization=None):
    state = ScamShieldState(message=message, claimed_organization=claimed_organization)
    result = graph.invoke(state)
    print(f"\n--- {label} ---")
    print("input:", repr(message))
    print("normalized urls:", result["urls"])
    print("score_breakdown:", result["score_breakdown"])
    print("risk_score:", result["risk_score"])
    print("risk_level:", result["risk_level"])
    print("confidence:", result["confidence"])
    print("reasoning_model:", result["reasoning_model"])
    return result


def url_only_breakdown(result):
    return sorted(
        (item for item in result["score_breakdown"] if item["signal"] in URL_SIGNAL_LABELS),
        key=lambda item: item["signal"],
    )


def render_and_ocr(text: str) -> str:
    """
    Draws `text` onto a real PNG (one line per '\\n' the caller already
    supplied — callers keep URLs on their own line so a naive word-wrap
    can't split a URL across two lines) and runs it through the real
    Tesseract OCR service.
    """
    image = Image.new("RGB", (1400, 500), "white")
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except OSError:
        font = ImageFont.load_default()
    draw.multiline_text((30, 30), text, fill="black", font=font, spacing=14)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        image.save(tmp.name)
        tmp_path = tmp.name

    try:
        return extract_text_from_image(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def encode_and_decode_qr(data: str) -> str:
    """Encodes `data` into a real QR image and decodes it with the real OpenCV decoder."""
    encoder = cv2.QRCodeEncoder_create()
    qr_image = encoder.encode(data)

    scale = 10
    big = cv2.resize(
        qr_image, (qr_image.shape[1] * scale, qr_image.shape[0] * scale), interpolation=cv2.INTER_NEAREST
    )
    bordered = cv2.copyMakeBorder(big, 40, 40, 40, 40, cv2.BORDER_CONSTANT, value=255)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        cv2.imwrite(tmp.name, bordered)
        tmp_path = tmp.name

    try:
        decoded = decode_qr_code(tmp_path)
        assert decoded == data, f"QR round-trip failed: encoded {data!r}, decoded {decoded!r}"
        return decoded
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# A. TEXT — full attack (URL + urgency + threat + call to action)
# ---------------------------------------------------------------------------
attack_message = (
    "URGENT! Your Microsoft account has been suspended. Click here: "
    f"{PHISHING_URL} Call 9998269178 immediately."
)
text_result = run("A. TEXT (full attack)", attack_message, claimed_organization="Microsoft")

# ---------------------------------------------------------------------------
# B. IMAGE — same content, but read back through the REAL OCR engine. Laid
# out one clause per line, with the URL alone on its own line, the way an
# actual SMS screenshot would render it — so OCR line-wrapping can't split
# the URL across two lines.
# ---------------------------------------------------------------------------
attack_message_for_screenshot = (
    "URGENT!\n"
    "Your Microsoft account has been suspended.\n"
    "Click here:\n"
    f"{PHISHING_URL}\n"
    "Call 9998269178 immediately."
)
ocr_text = render_and_ocr(attack_message_for_screenshot)
image_result = run("B. IMAGE (real OCR of the same content)", ocr_text, claimed_organization="Microsoft")

# ---------------------------------------------------------------------------
# C. QR — only the decoded URL, no surrounding message language, via the
#    REAL QR decoder
# ---------------------------------------------------------------------------
decoded_url = encode_and_decode_qr(PHISHING_URL)
qr_result = run("C. QR (real decode, URL only)", decoded_url, claimed_organization="Microsoft")

# ---------------------------------------------------------------------------
# D. Legitimate TEXT
# ---------------------------------------------------------------------------
legit_text_result = run(
    "D. Legitimate TEXT",
    f"Your Microsoft account security information was updated. You can review your security settings at {LEGITIMATE_URL}",
    claimed_organization="Microsoft",
)

# ---------------------------------------------------------------------------
# E. Legitimate QR
# ---------------------------------------------------------------------------
legit_decoded_url = encode_and_decode_qr(LEGITIMATE_URL)
legit_qr_result = run("E. Legitimate QR (real decode)", legit_decoded_url, claimed_organization="Microsoft")

# ---------------------------------------------------------------------------
# F/G. Generalization checks — different brand, bare URL, no claimed org.
# Not part of the strict assertions below, just evidence this isn't
# overfitted to one hardcoded domain.
# ---------------------------------------------------------------------------
run(
    "F. Netflix-style lookalike, TEXT",
    f"Your Netflix payment failed. Update your billing info now: {NETFLIX_LOOKALIKE_URL}",
    claimed_organization="Netflix",
)
run("G. Bare suspicious URL, no message language, no claimed org", BARE_URL)

# ---------------------------------------------------------------------------
# H. REGRESSION — the exact reported bug: a combosquat-shaped URL decoded
# from a QR code, with NO claimed_organization (the QR endpoint never
# requires one), must still produce URL-level evidence instead of scoring
# 0/LOW just because no brand was named. Decoded via the REAL QR decoder,
# exactly like the C/E cases above.
# ---------------------------------------------------------------------------
no_claim_decoded_url = encode_and_decode_qr(NO_CLAIM_COMBOSQUAT_URL)
no_claim_qr_result = run(
    "H. QR combosquat URL, no claimed_organization (regression)",
    no_claim_decoded_url,
)
no_claim_text_result = run(
    "H2. Same URL as TEXT, no claimed_organization (regression, cross-modal)",
    NO_CLAIM_COMBOSQUAT_URL,
)


# ---------------------------------------------------------------------------
# ASSERTIONS
# ---------------------------------------------------------------------------
print("\n\n=== CROSS-MODAL ASSERTIONS ===")

assert text_result["urls"] == [PHISHING_URL]
assert image_result["urls"] == [PHISHING_URL]
assert qr_result["urls"] == [PHISHING_URL]
print("PASS: identical normalized URL extracted from TEXT, real-OCR IMAGE, and real-decoded QR")

text_url_breakdown = url_only_breakdown(text_result)
image_url_breakdown = url_only_breakdown(image_result)
qr_url_breakdown = url_only_breakdown(qr_result)

assert text_url_breakdown == image_url_breakdown == qr_url_breakdown, (
    text_url_breakdown,
    image_url_breakdown,
    qr_url_breakdown,
)
print(f"PASS: identical URL/brand score contribution across TEXT/IMAGE/QR: {text_url_breakdown}")

# TEXT and IMAGE carry equivalent full evidence (URL + same message
# language) -> the complete deterministic score/level must match exactly.
assert text_result["risk_score"] == image_result["risk_score"]
assert text_result["risk_level"] == image_result["risk_level"]
print(
    f"PASS: TEXT and IMAGE with equivalent evidence produce the identical "
    f"deterministic score ({text_result['risk_score']}) and level ({text_result['risk_level']})"
)

# QR carries strictly less evidence (no surrounding message language), so
# it is legitimately allowed to score lower than the full SMS — but it
# must still carry the full URL/brand contribution, not near-zero.
url_only_score = sum(item["points"] for item in text_url_breakdown)
assert qr_result["risk_score"] == url_only_score
assert 0 < qr_result["risk_score"] < text_result["risk_score"]
print(
    f"PASS: QR-only score ({qr_result['risk_score']}) equals the URL/brand contribution alone "
    f"({url_only_score}) — legitimately lower than the full-message TEXT score "
    f"({text_result['risk_score']}) but not collapsed to near-zero"
)

# Legitimate domain must not be flagged, regardless of modality.
assert legit_text_result["risk_score"] == 0
assert legit_text_result["risk_level"] == "LOW"
assert legit_qr_result["risk_score"] == 0
assert legit_qr_result["risk_level"] == "LOW"
print("PASS: legitimate microsoft.com scores 0/LOW whether submitted as text or QR")

# risk_level must never contradict risk_score.
for label, result in [("TEXT", text_result), ("IMAGE", image_result), ("QR", qr_result)]:
    assert result["risk_level"] == derive_risk_level(result["risk_score"]), label
print("PASS: risk_level is always derived from risk_score via fixed thresholds (never contradicts it)")

# H. Regression: a combosquat-shaped URL with NO claimed_organization
# must not silently score 0 just because QR (or any bare-URL input)
# never named a brand.
assert no_claim_qr_result["risk_score"] > 0, no_claim_qr_result["risk_score"]
assert any(
    item["signal"] == "Lookalike domain compound structure"
    for item in no_claim_qr_result["score_breakdown"]
), no_claim_qr_result["score_breakdown"]
# And it must NOT contain a confirmed BRAND_IMPERSONATION claim — no
# organization was ever named, so ScamShield cannot claim to know one.
assert not any(
    item["signal"] == "Possible brand impersonation"
    for item in no_claim_qr_result["score_breakdown"]
), no_claim_qr_result["score_breakdown"]
# Same URL, no claimed org, submitted as TEXT instead of QR -> identical
# URL-level evidence (this was never a QR-specific fix).
assert no_claim_qr_result["score_breakdown"] == no_claim_text_result["score_breakdown"]
print(
    "PASS: combosquat-shaped URL with no claimed_organization now scores "
    f"{no_claim_qr_result['risk_score']} ({no_claim_qr_result['risk_level']}) instead of 0/LOW, "
    "identically whether submitted as QR or TEXT"
)

print("\nCross-modal consistency: PASS")
