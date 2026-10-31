from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse

from app.api._shared import run_investigation, stream_case
from app.api.uploads import read_image
from app.engine.analysis import SEV, Case
from app.models.investigation import QrTextRequest
from app.qr.analyze import case_from_payload, case_from_text
from app.qr.payload import classify
from app.services.qr import decode_all

router = APIRouter()
MAX_CODES = 5


def _decode(data: bytes) -> list[dict]:
    codes = decode_all(data)
    if not codes:
        raise HTTPException(status_code=422, detail="No QR code could be read in this image. Make sure the whole code is visible and in focus.")
    return codes[:MAX_CODES]


def _investigate_codes(codes: list[dict], claimed: str | None) -> dict:
    results = []
    for code in codes:
        case = case_from_payload(classify(code["text"]), claimed)
        results.append(run_investigation(case))
    worst = max(results, key=lambda r: (SEV[r["verdict"]], r["risk_score"]))
    out = dict(worst)
    if len(results) > 1:
        out["qr_codes"] = [
            {"decoded_text": r["decoded_text"], "verdict": r["verdict"], "risk_score": r["risk_score"], "qr": r["qr"]}
            for r in results
        ]
    return out


@router.post("/investigate/qr")
async def investigate_qr(file: UploadFile = File(...), claimed_organization: str | None = Form(None)):
    data, _ = await read_image(file)

    def work():
        return _investigate_codes(_decode(data), claimed_organization)

    return await run_in_threadpool(work)


@router.post("/investigate/qr/stream")
async def investigate_qr_stream(file: UploadFile = File(...), claimed_organization: str | None = Form(None)):
    data, _ = await read_image(file)

    def prepare() -> Case:
        codes = _decode(data)
        return case_from_payload(classify(codes[0]["text"]), claimed_organization)

    return StreamingResponse(
        stream_case(prepare, ("decode", "Decoding the QR code")),
        media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/investigate/qr-text")
def investigate_qr_text(request: QrTextRequest):
    """Analyse text already decoded on the user's device (live camera scanner)."""
    return run_investigation(case_from_text(request.text, request.claimed_organization))


@router.post("/investigate/qr-text/stream")
def investigate_qr_text_stream(request: QrTextRequest):
    return StreamingResponse(
        stream_case(lambda: case_from_text(request.text, request.claimed_organization)),
        media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
