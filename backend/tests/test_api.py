import shutil
from pathlib import Path

import pytest

from app.config import settings

SAMPLE = Path(__file__).parent / "sample_screenshot.png"
DEMO = {
    "message": "URGENT! Your Microsoft account has been suspended. Click here: https://miconsoft-login.com",
    "claimed_organization": "Microsoft",
}


def test_home(client):
    assert client.get("/").json()["project"] == "ScamShield"


def test_investigate_text(client):
    body = client.post("/investigate", json=DEMO).json()
    assert body["risk_level"] in {"HIGH", "CRITICAL"}
    assert body["reasoning_model"] == "mock-model"
    assert {"risk_score", "confidence", "reasons", "recommendation", "evidence", "score_breakdown"} <= body.keys()


def test_image_path_field_is_rejected(client):
    response = client.post("/investigate", json={"message": "hi", "image_path": "C:/Windows/win.ini"})
    assert response.status_code == 422


def test_unknown_field_is_rejected(client):
    assert client.post("/investigate", json={"message": "x", "foo": 1}).status_code == 422


def test_empty_message_is_rejected(client):
    assert client.post("/investigate", json={}).status_code == 422


def test_image_rejects_wrong_type(client):
    response = client.post("/investigate/image", files={"file": ("a.txt", b"hello", "text/plain")})
    assert response.status_code == 415


def test_image_rejects_empty_file(client):
    response = client.post("/investigate/image", files={"file": ("a.png", b"", "image/png")})
    assert response.status_code == 400


def test_image_ocr_unavailable_returns_503(client, monkeypatch):
    monkeypatch.setattr(settings, "tesseract_cmd", "C:/definitely/missing/tesseract.exe")
    response = client.post("/investigate/image", files={"file": ("a.png", SAMPLE.read_bytes(), "image/png")})
    assert response.status_code == 503


@pytest.mark.skipif(not (settings.tesseract_cmd or shutil.which("tesseract")), reason="Tesseract not installed")
def test_image_upload_runs_pipeline(client):
    response = client.post("/investigate/image", files={"file": ("a.png", SAMPLE.read_bytes(), "image/png")})
    assert response.status_code == 200
    assert response.json()["extracted_text"]


def test_qr_rejects_non_qr_image(client):
    response = client.post("/investigate/qr", files={"file": ("a.png", SAMPLE.read_bytes(), "image/png")})
    assert response.status_code == 422
