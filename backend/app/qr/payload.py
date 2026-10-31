"""
QR payload classification and analysis.

decode -> classify type -> type-specific checks. URL payloads are then sent
through the SAME link engine used for text messages, so a link scores the
same whether it was typed, read from a screenshot, or scanned.
"""

import re
from dataclasses import dataclass, field
from urllib.parse import parse_qs, unquote, urlsplit

from app.engine.signals import Signal, make
from app.intel.registry_data import UPI_HANDLES
from app.intel.trust import GENERIC_BRAND_WORDS, brand_tokens

DANGEROUS_SCHEMES = {"javascript", "data", "file", "vbscript", "blob", "ms-msdt", "search-ms", "intent", "market"}
SERVICE_SCHEMES = {
    "spotify": "Spotify", "whatsapp": "WhatsApp", "tg": "Telegram", "fb": "Facebook",
    "instagram": "Instagram", "youtube": "YouTube", "vnd.youtube": "YouTube", "twitter": "X / Twitter",
    "linkedin": "LinkedIn", "zoommtg": "Zoom", "zoomus": "Zoom", "slack": "Slack", "discord": "Discord",
    "paytmmp": "Paytm", "phonepe": "PhonePe", "tez": "Google Pay", "gpay": "Google Pay", "bhim": "BHIM",
    "itms-apps": "Apple App Store", "upi": "UPI",
}
PAYEE_RED_FLAGS = re.compile(r"\b(?:refund|support|customer care|helpline|kyc|lottery|prize|reward|winner|cashback|claim|tax|police|customs)\b", re.I)


@dataclass
class Payload:
    kind: str  # URL UPI WIFI VCARD TEL SMS MAILTO GEO CRYPTO DEEPLINK DANGEROUS EVENT TEXT
    raw: str
    fields: dict = field(default_factory=dict)
    title: str = ""
    signals: list[Signal] = field(default_factory=list)
    message: str = ""  # text fed to the message/link engine
    service: str | None = None


def _wifi(raw: str) -> dict:
    out = {}
    for key in ("S", "T", "P", "H"):
        m = re.search(rf"(?:^|;|:){key}:((?:\\.|[^;])*)", raw[5:])
        if m:
            out[key] = re.sub(r"\\(.)", r"\1", m.group(1))
    return out


def _upi(raw: str) -> dict:
    query = parse_qs(urlsplit(raw).query, keep_blank_values=True)
    return {k: unquote(v[0]) for k, v in query.items() if v}


def classify(raw: str) -> Payload:
    text = raw.strip()
    low = text.lower()

    # ---- schemes that run code or install things ----
    m = re.match(r"^([a-z][a-z0-9+.-]*):", low)
    scheme = m.group(1) if m else ""
    if scheme in DANGEROUS_SCHEMES:
        p = Payload("DANGEROUS", text, {"scheme": scheme}, "Unsafe link type", message="")
        p.signals.append(make("DANGEROUS_SCHEME", f"The QR uses '{scheme}:', which can run code or install apps instead of opening a web page.", "qr"))
        return p

    if scheme == "upi":
        return Payload("UPI", text, _upi(text), "UPI payment request", message=text)
    if low.startswith("wifi:"):
        fields = _wifi(text)
        p = Payload("WIFI", text, fields, "Wi-Fi network", message=f"Wi-Fi network {fields.get('S', '')}")
        if fields.get("T", "").lower() in {"nopass", ""} and not fields.get("P"):
            p.signals.append(make("OPEN_WIFI", "The Wi-Fi network has no password, so traffic is not encrypted.", "qr"))
        return p
    if low.startswith(("begin:vcard", "mecard:")):
        return Payload("VCARD", text, {}, "Contact card", message=text)
    if low.startswith("tel:"):
        return Payload("TEL", text, {"number": text[4:]}, "Phone number", message=f"Call {text[4:]}")
    if low.startswith(("sms:", "smsto:", "mms:")):
        rest = re.sub(r"^(?:sms|smsto|mms):", "", text, flags=re.I)
        number, _, body = rest.partition(":") if ":" in rest else rest.partition("?body=")
        number = number.split("?")[0]
        p = Payload("SMS", text, {"number": number, "body": body}, "Pre-filled SMS", message=body)
        if number and re.fullmatch(r"\+?\d{3,6}", number):
            p.signals.append(make("PREMIUM_SMS", f"Sending this SMS goes to the short code {number}, which can be a paid service.", "qr"))
        return p
    if low.startswith("mailto:"):
        return Payload("MAILTO", text, {"address": text[7:].split("?")[0]}, "Email", message=text[7:])
    if low.startswith("geo:"):
        return Payload("GEO", text, {"location": text[4:]}, "Map location", message="")
    if re.match(r"^(?:bitcoin|ethereum|litecoin|monero|dogecoin|bnb|solana|tron|usdt):", low):
        p = Payload("CRYPTO", text, {"coin": scheme}, "Cryptocurrency payment", message="")
        p.signals.append(make("CRYPTO_PAYMENT", "Cryptocurrency payments cannot be reversed once sent.", "qr"))
        return p
    if low.startswith("begin:vevent"):
        return Payload("EVENT", text, {}, "Calendar event", message=text)
    if scheme in SERVICE_SCHEMES and scheme != "upi":
        return Payload("DEEPLINK", text, {"scheme": scheme}, f"{SERVICE_SCHEMES[scheme]} app link", message="", service=SERVICE_SCHEMES[scheme])

    if re.match(r"^(?:https?|ftp)://", low) or re.match(r"^(?:www\.)?[a-z0-9-]+(?:\.[a-z0-9-]+)+(?:/|$|\?)", low):
        return Payload("URL", text, {}, "Web link", message=text)

    return Payload("TEXT", text, {}, "Text", message=text)


def analyze_upi(payload: Payload, context_text: str = "") -> dict:
    """Return the payee/amount summary and add UPI signals to the payload."""

    f = payload.fields
    vpa = (f.get("pa") or "").strip().lower()
    payee = (f.get("pn") or "").strip()
    amount = (f.get("am") or "").strip()
    summary = {
        "payee": payee or None, "vpa": vpa or None, "amount": amount or None,
        "currency": f.get("cu") or "INR", "note": f.get("tn") or None,
        "merchant_code": f.get("mc") or None, "reference": f.get("tr") or None,
    }
    add = payload.signals.append

    if not re.fullmatch(r"[a-z0-9._-]{2,64}@[a-z0-9]{2,32}", vpa):
        add(make("UPI_MALFORMED", "The payment address (VPA) is missing or not in the normal name@bank format.", "qr"))
        return summary

    local, handle = vpa.split("@", 1)
    if handle not in UPI_HANDLES:
        add(make("UPI_UNKNOWN_HANDLE", f"'@{handle}' is not a recognised UPI bank handle.", "qr"))

    mismatch = None
    if payee:
        if PAYEE_RED_FLAGS.search(payee):
            mismatch = f"The payee name '{payee}' sounds like an official refund/support desk, which real people do not collect money through."
        else:
            for token, brand in brand_tokens().items():
                if len(token) >= 4 and token not in GENERIC_BRAND_WORDS and re.search(rf"\b{re.escape(token)}\b", payee.lower()):
                    brand_labels = {d.split(".")[0] for d in brand.domains}
                    if token not in local and not (brand_labels & set(re.split(r"[^a-z0-9]+", local))):
                        mismatch = f"The payee name mentions {brand.name}, but the payment address '{vpa}' does not look like {brand.name}'s."
                        break
    if mismatch:
        add(make("UPI_BRAND_PAYEE_MISMATCH", mismatch, "qr"))

    if not any(s.polarity == "risk" for s in payload.signals):
        add(make("UPI_VALID", "A well-formed UPI payment request with a recognised bank handle.", "qr"))
    return summary
