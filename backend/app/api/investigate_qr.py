import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.api._shared import run_investigation
from app.graph.state import ScamShieldState
from app.services.qr import decode_qr_code


router = APIRouter()

ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
MAX_UPLOAD_BYTES = 8 * 1024 * 1024  # 8 MB


@router.post("/investigate/qr")
async def investigate_qr(
    file: UploadFile = File(...),
    claimed_organization: str | None = Form(None),
):
    """
    QR image -> OpenCV QR decoder (services/qr.py) -> decoded text/URL ->
    the SAME ScamShield investigation engine used for SMS/text (extraction,
    URL investigation, identity verification, social engineering, Gemini
    reasoning). No separate scam-detection logic for QR codes.
    """

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Unsupported image type. Upload a PNG, JPEG, or WEBP QR code image.",
        )

    contents = await file.read()

    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image is too large (max 8 MB).")

    suffix = Path(file.filename or "qr.png").suffix or ".png"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        decoded_text = decode_qr_code(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if not decoded_text:
        raise HTTPException(
            status_code=422,
            detail="No QR code could be decoded from the uploaded image.",
        )

    state = ScamShieldState(
        message=decoded_text,
        source="qr_code",
        claimed_organization=claimed_organization,
    )

    result = run_investigation(state)
    result["decoded_text"] = decoded_text
    return result
