"""
Real-browser sandbox via urlscan.io.

urlscan opens the link in an isolated browser on ITS machines and reports what
the page really did: where it ended up, what it looked like, how old the domain
is, and whether it is malicious. Nothing runs on this server or the user's
device. Pages that only appear after JavaScript runs are invisible to our text
inspector, so this is the layer that sees them.

Without a key: searches earlier public scans of the same site (free).
With URLSCAN_API_KEY: submits a new scan as "unlisted" (not shown publicly,
because links can contain personal tokens) and waits briefly for the result.
Everything fails soft: an outage only lowers coverage.
"""

import threading
import time
from dataclasses import dataclass

import httpx

from app.config import settings
from app.engine.signals import Signal, make
from app.intel.urls import ParsedUrl

API = "https://urlscan.io/api/v1"
FIRST_POLL_DELAY = 8.0
_cache: dict[str, tuple[float, "SandboxResult"]] = {}
_lock = threading.Lock()
_fail_until = 0.0
_fails = 0


@dataclass
class SandboxResult:
    status: str  # done | none | unavailable | skipped
    source: str = ""  # live_scan | earlier_scan
    malicious: bool | None = None
    score: int | None = None
    brands: tuple = ()
    final_url: str = ""
    title: str = ""
    screenshot: str = ""
    report: str = ""
    domain_age_days: int | None = None
    tls_age_days: int | None = None
    scanned_at: str = ""
    detail: str = ""

    def to_dict(self) -> dict:
        d = dict(self.__dict__)
        d["brands"] = list(self.brands)
        return d


def _headers() -> dict:
    return {"API-Key": settings.urlscan_api_key} if settings.urlscan_api_key else {}


def _record(ok: bool):
    global _fails, _fail_until
    if ok:
        _fails = 0
    else:
        _fails += 1
        if _fails >= 3:
            _fail_until, _fails = time.time() + 300, 0


def _from_page(item: dict, source: str) -> SandboxResult:
    page = item.get("page", {}) or {}
    task = item.get("task", {}) or {}
    uuid = task.get("uuid") or item.get("_id") or ""
    return SandboxResult(
        "done", source, final_url=page.get("url", ""), title=page.get("title", "") or "",
        screenshot=item.get("screenshot") or task.get("screenshotURL") or (f"https://urlscan.io/screenshots/{uuid}.png" if uuid else ""),
        report=f"https://urlscan.io/result/{uuid}/" if uuid else "",
        domain_age_days=page.get("apexDomainAgeDays"), tls_age_days=page.get("tlsAgeDays"), scanned_at=task.get("time", ""),
    )


def _apply_verdicts(result: SandboxResult, data: dict) -> SandboxResult:
    overall = (data.get("verdicts") or {}).get("overall") or {}
    if overall:
        result.malicious = bool(overall.get("malicious"))
        result.score = overall.get("score")
        result.brands = tuple(overall.get("brands") or ())
    return result


def _search(client: httpx.Client, parsed: ParsedUrl) -> SandboxResult | None:
    host = parsed.host_ascii
    r = client.get(f"{API}/search/", params={"q": f'task.domain:"{host}" AND date:>now-30d', "size": 1}, headers=_headers())
    r.raise_for_status()
    results = r.json().get("results") or []
    return _from_page(results[0], "earlier_scan") if results else None


def _submit(client: httpx.Client, url: str, budget: float) -> SandboxResult | None:
    r = client.post(f"{API}/scan/", json={"url": url, "visibility": "unlisted"}, headers=_headers())
    if r.status_code in {400, 422}:  # urlscan refuses some domains; not an outage
        return None
    r.raise_for_status()
    uuid = r.json()["uuid"]
    deadline = time.time() + budget
    time.sleep(min(FIRST_POLL_DELAY, budget))
    while time.time() < deadline:
        rr = client.get(f"{API}/result/{uuid}/", headers=_headers())
        if rr.status_code == 200:
            data = rr.json()
            data.setdefault("task", {})["uuid"] = uuid
            return _apply_verdicts(_from_page(data, "live_scan"), data)
        if rr.status_code != 404:
            rr.raise_for_status()
        time.sleep(2.0)
    return None


def scan(parsed: ParsedUrl, budget: float = 22.0) -> SandboxResult:
    if not settings.enable_sandbox:
        return SandboxResult("skipped", detail="turned off")
    key = parsed.url
    with _lock:
        item = _cache.get(key)
    if item and time.time() - item[0] < 6 * 3600:
        return item[1]
    if time.time() < _fail_until:
        return SandboxResult("unavailable", detail="temporarily disabled")

    try:
        with httpx.Client(timeout=httpx.Timeout(6.0, connect=3.0), follow_redirects=True) as client:
            result = None
            if settings.urlscan_api_key:
                result = _submit(client, parsed.url, budget)
            if result is None:
                result = _search(client, parsed)
        _record(True)
    except Exception as err:  # noqa: BLE001
        _record(False)
        return SandboxResult("unavailable", detail=type(err).__name__)

    result = result or SandboxResult("none", detail="no sandbox scan available for this site")
    with _lock:
        _cache[key] = (time.time(), result)
    return result


def to_signals(parsed: ParsedUrl, result: SandboxResult, have_age: bool) -> list[Signal]:
    if result.status != "done":
        return []
    t = parsed.key
    out: list[Signal] = []
    if result.malicious:
        out.append(make("SANDBOX_MALICIOUS", f"A real browser sandbox opened this page and judged it malicious{f' (imitating {result.brands[0]})' if result.brands else ''}.", "sandbox", t))
    elif result.malicious is False and result.source == "live_scan":
        out.append(make("SANDBOX_CLEAN", "A real browser sandbox opened this page and found nothing malicious.", "sandbox", t))
    age = result.domain_age_days
    if not have_age and isinstance(age, int) and age >= 0:
        if age < 30:
            out.append(make("DOMAIN_AGE_LT_30D", f"{parsed.registrable} is only {age} day(s) old.", "sandbox", t))
        elif age < 365:
            out.append(make("DOMAIN_AGE_LT_1Y", f"{parsed.registrable} is {age // 30} month(s) old.", "sandbox", t))
    return out
