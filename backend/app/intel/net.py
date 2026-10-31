"""
Safe outbound fetching.

The resolver only ever downloads TEXT (never executes anything), refuses
private / loopback / metadata addresses on every hop (SSRF guard), and caps
time, hops and bytes. It never runs JavaScript or opens a browser.
"""

import ipaddress
import socket
import ssl
import time
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlsplit

import httpx

MAX_HOPS = 8
MAX_BYTES = 256 * 1024
TOTAL_BUDGET = 10.0  # seconds for the whole chain
ALLOWED_PORTS = {80, 443, 8080, 8443}
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


class BlockedHost(Exception):
    pass


def is_public_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return not (
        addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_multicast
        or addr.is_reserved or addr.is_unspecified
        or (addr.version == 4 and addr in ipaddress.ip_network("100.64.0.0/10"))
    )


def resolve_public(host: str) -> list[str]:
    """Resolve host; raise BlockedHost if ANY address is non-public."""

    try:
        ipaddress.ip_address(host)
        addresses = [host]
    except ValueError:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
        addresses = sorted({info[4][0] for info in infos})
    if not addresses:
        raise socket.gaierror("no addresses")
    for address in addresses:
        if not is_public_ip(address):
            raise BlockedHost(f"{host} resolves to a non-public address")
    return addresses


@dataclass
class FetchResult:
    outcome: str  # OK NXDOMAIN NOT_FOUND CONNECT_FAILED TIMEOUT TLS_ERROR BLOCKED LOOP TOO_MANY_HOPS SERVER_ERROR ERROR
    final_url: str
    status: int | None = None
    chain: list[str] = field(default_factory=list)
    body: str = ""
    content_type: str = ""
    detail: str = ""

    @property
    def reachable(self) -> bool:
        return self.outcome in {"OK", "SERVER_ERROR"}


def fetch(url: str, want_body: bool = False, timeout: float = 4.0) -> FetchResult:
    chain = [url]
    current = url
    seen = {url}
    started = time.time()

    with httpx.Client(
        follow_redirects=False,
        timeout=httpx.Timeout(timeout, connect=3.0),
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,*/*;q=0.5"},
        verify=True,
    ) as client:
        for _ in range(MAX_HOPS + 1):
            if time.time() - started > TOTAL_BUDGET:
                return FetchResult("TIMEOUT", current, chain=chain, detail="timed out")
            parts = urlsplit(current)
            host = parts.hostname or ""
            port = parts.port or (443 if parts.scheme == "https" else 80)
            if parts.scheme not in {"http", "https"} or port not in ALLOWED_PORTS:
                return FetchResult("BLOCKED", current, chain=chain, detail="unsupported scheme or port")
            try:
                resolve_public(host)
            except BlockedHost as err:
                return FetchResult("BLOCKED", current, chain=chain, detail=str(err))
            except socket.gaierror:
                return FetchResult("NXDOMAIN", current, chain=chain, detail=f"{host} does not exist")
            except OSError as err:
                return FetchResult("ERROR", current, chain=chain, detail=str(err))

            try:
                with client.stream("GET", current) as response:
                    status = response.status_code
                    ctype = response.headers.get("content-type", "")
                    if status in {301, 302, 303, 307, 308} and response.headers.get("location"):
                        nxt = urljoin(current, response.headers["location"])
                        if nxt in seen:
                            return FetchResult("LOOP", nxt, status, chain, detail="redirect loop")
                        seen.add(nxt)
                        chain.append(nxt)
                        current = nxt
                        continue

                    body = ""
                    if want_body and "text/html" in ctype.lower():
                        raw = b""
                        for piece in response.iter_bytes():
                            raw += piece
                            if len(raw) >= MAX_BYTES or time.time() - started > TOTAL_BUDGET:
                                break
                        body = raw[:MAX_BYTES].decode(response.encoding or "utf-8", errors="replace")

                    if status in {404, 410}:
                        return FetchResult("NOT_FOUND", current, status, chain, body, ctype, "page not found")
                    if status >= 500:
                        return FetchResult("SERVER_ERROR", current, status, chain, body, ctype)
                    return FetchResult("OK", current, status, chain, body, ctype)
            except httpx.TimeoutException:
                return FetchResult("TIMEOUT", current, chain=chain, detail="timed out")
            except httpx.ConnectError as err:
                text = str(err)
                if "CERTIFICATE" in text.upper() or "SSL" in text.upper():
                    return FetchResult("TLS_ERROR", current, chain=chain, detail=text[:120])
                return FetchResult("CONNECT_FAILED", current, chain=chain, detail=text[:120])
            except ssl.SSLError as err:
                return FetchResult("TLS_ERROR", current, chain=chain, detail=str(err)[:120])
            except httpx.HTTPError as err:
                return FetchResult("ERROR", current, chain=chain, detail=str(err)[:120])

    return FetchResult("TOO_MANY_HOPS", current, chain=chain, detail="too many redirects")
