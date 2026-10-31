from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api._shared import run_investigation, stream_case
from app.engine.analysis import Case
from app.models.investigation import InvestigationRequest

router = APIRouter()


def _case(request: InvestigationRequest) -> Case:
    return Case(
        message=request.message,
        claimed_organization=request.claimed_organization,
        source=request.source,
        kind="text",
    )


@router.post("/investigate")
def investigate(request: InvestigationRequest):
    return run_investigation(_case(request))


@router.post("/investigate/stream")
def investigate_stream(request: InvestigationRequest):
    return StreamingResponse(stream_case(lambda: _case(request)), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
