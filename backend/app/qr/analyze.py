from app.engine.analysis import Case
from app.engine.signals import make
from app.qr.payload import Payload, analyze_upi, classify


def case_from_payload(payload: Payload, claimed: str | None = None, context_text: str = "") -> Case:
    summary = None
    if payload.kind == "UPI":
        summary = analyze_upi(payload, context_text)
    if payload.kind == "DEEPLINK" and payload.service:
        payload.signals.append(make("VERIFIED_SERVICE", f"This QR opens the {payload.service} app.", "qr"))

    qr_info = {
        "kind": payload.kind,
        "title": payload.title,
        "raw": payload.raw,
        "fields": {k: v for k, v in payload.fields.items() if k != "P"},  # never echo Wi-Fi passwords
        "summary": summary,
        "service": {"name": payload.service, "verified": True} if payload.service else None,
    }
    text = payload.message or ""
    if context_text:
        text = f"{context_text}\n{text}".strip()
    return Case(
        message=text,
        claimed_organization=claimed,
        source="qr_code",
        kind="qr",
        extra_signals=list(payload.signals),
        extra={"qr": qr_info, "decoded_text": payload.raw},
    )


def case_from_text(text: str, claimed: str | None = None) -> Case:
    return case_from_payload(classify(text), claimed)
