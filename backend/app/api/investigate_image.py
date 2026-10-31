import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.api._shared import run_investigation
from app.graph.state import ScamShieldState
from app.services.ocr import OcrUnavailable, extract_text_from_image


router = APIRouter()

ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
MAX_UPLOAD_BYTES = 8 * 1024 * 1024  # 8 MB


@router.post("/investigate/image")
async def investigate_image(
    file: UploadFile = File(...),
    claimed_organization: str | None = Form(None),
    source: str = Form("sms_image"),
):
    """
    SMS screenshot -> temporary local file -> existing Tesseract OCR
    service (services/ocr.py, unmodified) -> the extracted text is fed
    into the SAME ScamShieldState.message field a normal text submission
    uses, so it goes through the full existing investigation pipeline
    (extraction, URL, identity, social-engineering, Gemini reasoning)
    instead of only being appended as a late piece of evidence.
    """

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Unsupported image type. Upload a PNG, JPEG, or WEBP screenshot.",
        )

    contents = await file.read()

    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image is too large (max 8 MB).")

    suffix = Path(file.filename or "screenshot.png").suffix or ".png"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name

    try:
        extracted_text = extract_text_from_image(tmp_path)
    except OcrUnavailable as err:
        raise HTTPException(status_code=503, detail=str(err)) from err
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    initial_evidence = []
    if not extracted_text:
        initial_evidence.append(
            "No readable text was extracted from the uploaded image via OCR."
        )

    state = ScamShieldState(
        message=extracted_text,
        source=source,
        claimed_organization=claimed_organization,
        evidence=initial_evidence,
    )

    result = run_investigation(state)
    result["extracted_text"] = extracted_text
    return result
