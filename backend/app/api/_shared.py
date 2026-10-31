import json
from collections.abc import Callable, Iterator

from fastapi import HTTPException

from app.engine.analysis import Case
from app.graph import graph as pipeline

ORDER = ["extract", "message", "urls", "decide", "explain"]


def run_investigation(case: Case) -> dict:
    return pipeline.run(case).result


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


def _stage(stage_id: str, status: str, detail: str = "") -> str:
    label = pipeline.STAGE_LABELS.get(stage_id, stage_id)
    return sse("stage", {"id": stage_id, "label": label, "status": status, "detail": detail})


def stream_case(prepare: Callable[[], Case], pre_stage: tuple[str, str] | None = None) -> Iterator[str]:
    """
    Server-sent events for one investigation. `prepare` builds the Case (and
    may do OCR / QR decoding first). Events: stage, partial, verdict,
    explanation, done, error.
    """
    try:
        if pre_stage:
            yield sse("stage", {"id": pre_stage[0], "label": pre_stage[1], "status": "start", "detail": ""})
        case = prepare()
        if pre_stage:
            yield sse("stage", {"id": pre_stage[0], "label": pre_stage[1], "status": "done", "detail": ""})

        yield _stage(ORDER[0], "start")
        for name, state in pipeline.stream(case):
            case = state
            detail = ""
            if name == "extract":
                detail = f"{len(case.urls)} link(s) found"
            elif name == "urls":
                detail = ", ".join(f"{r.registrable}: {r.verdict}" for r in case.url_reports) or "no links to check"
                yield sse("partial", {"urls": [r.to_dict() for r in case.url_reports]})
            elif name == "decide":
                r = case.result
                yield sse("verdict", {k: r[k] for k in ("verdict", "risk_score", "risk_level", "confidence", "confidence_factors", "decision_path")})
            yield _stage(name, "done", detail)
            idx = ORDER.index(name)
            if idx + 1 < len(ORDER):
                yield _stage(ORDER[idx + 1], "start")
        r = case.result
        yield sse("explanation", {"reasons": r["reasons"], "recommendation": r["recommendation"], "reasoning_model": r["reasoning_model"]})
        yield sse("done", r)
    except HTTPException as err:
        yield sse("error", {"status": err.status_code, "message": str(err.detail)})
    except Exception as err:  # noqa: BLE001
        yield sse("error", {"status": 500, "message": "Something went wrong while analysing this content."})
