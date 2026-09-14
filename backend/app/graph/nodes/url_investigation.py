from urllib.parse import urlparse

from app.graph.state import ScamShieldState
from app.graph.signals import make_signal
from app.services.url_normalize import normalize_url


SUSPICIOUS_KEYWORDS = [
    "login",
    "verify",
    "verification",
    "secure",
    "security",
    "account",
    "update",
    "confirm",
    "bank",
    "signin",
]


def investigate_url(url: str) -> list[str]:
    """
    Perform basic deterministic security checks on a URL.
    """

    findings = []

    parsed = urlparse(url)
    hostname = parsed.hostname or ""

    # Check whether HTTPS is used
    if parsed.scheme != "https":
        findings.append("URL does not use HTTPS.")

    # Check for suspicious keywords
    lowered_url = url.lower()

    for keyword in SUSPICIOUS_KEYWORDS:
        if keyword in lowered_url:
            findings.append(
                f"URL contains suspicious keyword: '{keyword}'."
            )

    # Check for IP address instead of a domain name
    hostname_parts = hostname.split(".")

    if hostname.replace(".", "").isdigit():
        findings.append("URL uses an IP address instead of a domain name.")

    # Check for excessive subdomains
    if len(hostname_parts) > 4:
        findings.append("URL contains an unusually large number of subdomains.")

    return findings


def url_investigation_node(state: ScamShieldState) -> ScamShieldState:
    """
    Investigate every URL extracted from the message. Deterministic
    findings are recorded both as human-readable evidence[] strings (for
    display and for Gemini's prompt) and as structured RiskSignal entries
    keyed to the URL's normalized form (for scoring) — so the SAME
    destination scores the same whether it was typed, OCR'd, or decoded
    from a QR code.
    """

    all_findings = []
    new_signals = []

    for url in state.urls:
        normalized = normalize_url(url)
        findings = investigate_url(url)

        for finding in findings:
            all_findings.append(f"{url}: {finding}")

            if "does not use https" in finding.lower():
                new_signals.append(
                    make_signal("URL_INSECURE", finding, "url_investigation", target=normalized)
                )
            elif finding.lower().startswith("url contains suspicious keyword"):
                new_signals.append(
                    make_signal(
                        "URL_SUSPICIOUS_KEYWORD", finding, "url_investigation", target=normalized
                    )
                )
            elif "ip address instead of a domain" in finding.lower():
                new_signals.append(
                    make_signal("URL_RAW_IP", finding, "url_investigation", target=normalized)
                )
            elif "unusually large number of subdomains" in finding.lower():
                new_signals.append(
                    make_signal(
                        "URL_EXCESSIVE_SUBDOMAINS", finding, "url_investigation", target=normalized
                    )
                )

    state.evidence.extend(all_findings)
    state.signals.extend(new_signals)

    return state
