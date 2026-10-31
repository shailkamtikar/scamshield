from fastapi import APIRouter

from app.api._shared import run_investigation
from app.models.investigation import InvestigationRequest
from app.graph.state import ScamShieldState


router = APIRouter()


@router.post("/investigate")
def investigate(request: InvestigationRequest):
    state = ScamShieldState(
        message=request.message,
        source=request.source,
        claimed_organization=request.claimed_organization,
    )

    return run_investigation(state)
