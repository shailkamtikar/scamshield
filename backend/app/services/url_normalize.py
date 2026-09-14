from urllib.parse import urlparse


def normalize_url(url: str) -> str:
    """
    Canonical form of a URL used to recognize the SAME destination
    regardless of how ScamShield received it (typed in a text message,
    read off a screenshot via OCR, or decoded from a QR code).

    "https://Miconsoft-Login.com/", "http://www.miconsoft-login.com" and
    "miconsoft-login.com" all normalize to the same value, so evidence
    about that domain is recognized as one signal instead of being
    silently duplicated or treated as unrelated across modalities.
    """

    candidate = url.strip()
    if "://" not in candidate:
        candidate = f"https://{candidate}"

    parsed = urlparse(candidate)
    host = (parsed.hostname or "").lower()

    if host.startswith("www."):
        host = host[4:]

    path = parsed.path.rstrip("/")

    return f"{host}{path}"
