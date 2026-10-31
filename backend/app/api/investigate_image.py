from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse

from app.api._shared import run_investigation, stream_case
from app.api.uploads import read_image
from app.engine.analysis import Case
from app.engine.signals import make
from app.intel.urls import extract_urls
from app.services import ocr, vision

router = APIRouter()


def build_case(data: bytes, mime: str, claimed: str | None, source: str) -> Case:
    """Screenshot -> OCR (+ Gemini vision cross-check) -> the normal pipeline."""

    try:
        ocr_result = ocr.extract_text(data)
    except ocr.OcrUnavailable as err:
        raise HTTPException(status_code=503, detail=str(err)) from err
    read = vision.read_image(data, mime)

    text = ocr_result.text
    sender = ""
    extra_signals = []
    method = "ocr"
    if read and read.readable and read.text.strip():
        sender = read.sender.strip()
        ocr_urls = {u.key for u in extract_urls(ocr.repair_url_text(ocr_result.text))}
        vis_urls = extract_urls(read.text)
        if ocr_result.confidence < 65 or ocr_result.words < 6:
            text, method = read.text, "vision"
        else:
            method = "ocr+vision"
            missing = [u.url for u in vis_urls if u.key not in ocr_urls]
            if missing:
                text = text + "\n" + "\n".join(missing)
        if ocr_urls and {u.key for u in vis_urls} and ocr_urls != {u.key for u in vis_urls}:
            extra_signals.append(make("OCR_VISION_MISMATCH", "Two independent readers disagreed about a link in the screenshot; both were checked.", "image"))
    text = ocr.repair_url_text(text)

    if len(text.strip()) < 3:
        raise HTTPException(status_code=422, detail="No readable text was found in this image. Try a sharper, uncropped screenshot.")

    return Case(
        message=text,
        claimed_organization=claimed,
        source=sender or source,
        kind="image",
        extra_signals=extra_signals,
        extra={
            "extracted_text": text,
            "extraction": {
                "method": method,
                "ocr_confidence": round(ocr_result.confidence, 1),
                "ocr_words": ocr_result.words,
                "sender": sender or None,
                "vision_used": read is not None,
            },
        },
    )


@router.post("/investigate/image")
async def investigate_image(
    file: UploadFile = File(...),
    claimed_organization: str | None = Form(None),
    source: str = Form("sms_image"),
):
    data, mime = await read_image(file)
    return await run_in_threadpool(lambda: run_investigation(build_case(data, mime, claimed_organization, source)))


@router.post("/investigate/image/stream")
async def investigate_image_stream(
    file: UploadFile = File(...),
    claimed_organization: str | None = Form(None),
    source: str = Form("sms_image"),
):
    data, mime = await read_image(file)
    return StreamingResponse(
        stream_case(lambda: build_case(data, mime, claimed_organization, source), ("read", "Reading the screenshot (OCR + visual check)")),
        media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
