"""
Threat-intelligence lookups (free tiers). Every provider is optional and
fails soft: a missing key, quota, timeout or outage yields status
'unavailable' and the engine simply has less coverage (lower confidence).
"""

import base64
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import httpx

from app.config import settings
from app.engine.signals import Signal, make
from app.intel.urls import ParsedUrl

CACHE_DIR = Path(__file__).resolve().parents[3] / "data" / "cache"
_TTL = 24 * 3600
_cache: dict[tuple[str, str], tuple[float, "RepResult"]] = {}
_lock = threading.Lock()


@dataclass
class RepResult:
    provider: str
    status: str  # hit | clean | unavailable | skipped
    detail: str = ""
    malicious: int = 0  # engines/records that flagged it


def _cached(provider: str, key: str):
    with _lock:
        item = _cache.get((provider, key))
    if item and time.time() - item[0] < _TTL:
        return item[1]
    return None


def _store(provider: str, key: str, result: RepResult):
    if result.status != "unavailable":
        with _lock:
            _cache[(provider, key)] = (time.time(), result)
    return result


class _Breaker:
    """Stops calling a provider for a while after repeated failures."""

    def __init__(self, threshold=3, cooldown=300):
        self.fails, self.threshold, self.cooldown, self.until = 0, threshold, cooldown, 0.0

    def open(self) -> bool:
        return time.time() < self.until

    def record(self, ok: bool):
        if ok:
            self.fails = 0
        else:
            self.fails += 1
            if self.fails >= self.threshold:
                self.until, self.fails = time.time() + self.cooldown, 0


class _Bucket:
    def __init__(self, per_minute: int):
        self.per_minute, self.stamps, self.lock = per_minute, [], threading.Lock()

    def take(self) -> bool:
        now = time.time()
        with self.lock:
            self.stamps = [t for t in self.stamps if now - t < 60]
            if len(self.stamps) >= self.per_minute:
                return False
            self.stamps.append(now)
            return True


_breakers = {n: _Breaker() for n in ("safebrowsing", "virustotal", "urlhaus", "openphish")}
_vt_bucket = _Bucket(4)


def _client() -> httpx.Client:
    return httpx.Client(timeout=httpx.Timeout(6.0, connect=3.0), follow_redirects=True)


# ---------------- Google Safe Browsing (v4 Lookup) ----------------
def check_safe_browsing(url: str) -> RepResult:
    name = "Google Safe Browsing"
    if not settings.safe_browsing_api_key:
        return RepResult(name, "skipped", "no API key")
    if cached := _cached(name, url):
        return cached
    if _breakers["safebrowsing"].open():
        return RepResult(name, "unavailable", "temporarily disabled")
    body = {
        "client": {"clientId": "scamshield", "clientVersion": "2.0"},
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}],
        },
    }
    try:
        with _client() as c:
            r = c.post(
                "https://safebrowsing.googleapis.com/v4/threatMatches:find",
                params={"key": settings.safe_browsing_api_key},
                json=body,
            )
        r.raise_for_status()
        matches = r.json().get("matches", [])
        _breakers["safebrowsing"].record(True)
        if matches:
            kinds = sorted({m.get("threatType", "?") for m in matches})
            return _store(name, url, RepResult(name, "hit", ", ".join(kinds), len(matches)))
        return _store(name, url, RepResult(name, "clean"))
    except Exception as err:  # noqa: BLE001
        _breakers["safebrowsing"].record(False)
        return RepResult(name, "unavailable", type(err).__name__)


# ---------------- VirusTotal (domain report; never submits scans) ----------------
def check_virustotal(host: str) -> RepResult:
    name = "VirusTotal"
    if not settings.virustotal_api_key:
        return RepResult(name, "skipped", "no API key")
    if cached := _cached(name, host):
        return cached
    if _breakers["virustotal"].open():
        return RepResult(name, "unavailable", "temporarily disabled")
    if not _vt_bucket.take():
        return RepResult(name, "unavailable", "rate limit reached")
    try:
        with _client() as c:
            r = c.get(f"https://www.virustotal.com/api/v3/domains/{host}", headers={"x-apikey": settings.virustotal_api_key})
        if r.status_code == 404:
            return _store(name, host, RepResult(name, "clean", "not seen before"))
        r.raise_for_status()
        stats = r.json()["data"]["attributes"].get("last_analysis_stats", {})
        bad = int(stats.get("malicious", 0)) + int(stats.get("phishing", 0))
        _breakers["virustotal"].record(True)
        if bad:
            return _store(name, host, RepResult(name, "hit", f"{bad} engines flagged it", bad))
        return _store(name, host, RepResult(name, "clean"))
    except Exception as err:  # noqa: BLE001
        _breakers["virustotal"].record(False)
        return RepResult(name, "unavailable", type(err).__name__)


# ---------------- URLhaus ----------------
def check_urlhaus(url: str, host: str, host_level: bool = True) -> RepResult:
    name = "URLhaus"
    if not settings.urlhaus_auth_key:
        return RepResult(name, "skipped", "no Auth-Key")
    if cached := _cached(name, url):
        return cached
    if _breakers["urlhaus"].open():
        return RepResult(name, "unavailable", "temporarily disabled")
    headers = {"Auth-Key": settings.urlhaus_auth_key}
    try:
        with _client() as c:
            r = c.post("https://urlhaus-api.abuse.ch/v1/url/", data={"url": url}, headers=headers)
            r.raise_for_status()
            data = r.json()
            exact = data.get("query_status") == "ok"
            host_hit = False
            if not exact and host_level:
                # Whole-host listing only counts for unknown sites and only while a listed URL is still online;
                # popular hosts (github, httpbin, ...) have a few abused URLs but are not malicious as a whole.
                r = c.post("https://urlhaus-api.abuse.ch/v1/host/", data={"host": host}, headers=headers)
                r.raise_for_status()
                hd = r.json()
                host_hit = hd.get("query_status") == "ok" and any(u.get("url_status") == "online" for u in hd.get("urls", []))
        _breakers["urlhaus"].record(True)
        if exact:
            return _store(name, url, RepResult(name, "hit", "this exact link is listed in the URLhaus malware database", 1))
        if host_hit:
            return _store(name, url, RepResult(name, "hit", "this site currently hosts malware listed in URLhaus", 1))
        return _store(name, url, RepResult(name, "clean"))
    except Exception as err:  # noqa: BLE001
        _breakers["urlhaus"].record(False)
        return RepResult(name, "unavailable", type(err).__name__)


# ---------------- OpenPhish community feed ----------------
_phish_set: set[str] = set()
_phish_loaded = 0.0
_phish_lock = threading.Lock()


def _norm(u: str) -> str:
    return u.strip().lower().removeprefix("https://").removeprefix("http://").removeprefix("www.").rstrip("/")


def load_openphish(force: bool = False) -> int:
    global _phish_set, _phish_loaded
    with _phish_lock:
        if not force and _phish_set and time.time() - _phish_loaded < 12 * 3600:
            return len(_phish_set)
        cache = CACHE_DIR / "openphish.txt"
        text = ""
        try:
            if not force and cache.exists() and time.time() - cache.stat().st_mtime < 12 * 3600:
                text = cache.read_text(encoding="utf-8")
            else:
                with _client() as c:
                    r = c.get("https://openphish.com/feed.txt")
                r.raise_for_status()
                text = r.text
                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                cache.write_text(text, encoding="utf-8")
        except Exception:  # noqa: BLE001
            if cache.exists():
                text = cache.read_text(encoding="utf-8")
        _phish_set = {_norm(line) for line in text.splitlines() if line.strip()}
        _phish_loaded = time.time()
        return len(_phish_set)


def check_openphish(url: str) -> RepResult:
    name = "OpenPhish"
    load_openphish()
    if not _phish_set:
        return RepResult(name, "unavailable", "feed not loaded")
    if _norm(url) in _phish_set:
        return RepResult(name, "hit", "listed in the OpenPhish phishing feed", 1)
    return RepResult(name, "clean")


# ---------------- aggregate ----------------
def check_all(parsed: ParsedUrl, trusted: bool, use_virustotal: bool) -> list[RepResult]:
    """Run every provider concurrently. `trusted` domains skip VirusTotal to save its small quota."""

    url = parsed.url
    jobs = [lambda: check_safe_browsing(url), lambda: check_openphish(url), lambda: check_urlhaus(url, parsed.host_ascii, host_level=not trusted)]
    if not trusted:
        if use_virustotal:
            jobs.append(lambda: check_virustotal(parsed.host_ascii))
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        futures = [pool.submit(job) for job in jobs]
        results = []
        for f in futures:
            try:
                results.append(f.result(timeout=7))
            except Exception:  # noqa: BLE001
                results.append(RepResult("provider", "unavailable", "timeout"))
    return results


def to_signals(parsed: ParsedUrl, results: list[RepResult]) -> list[Signal]:
    signals: list[Signal] = []
    target = parsed.key
    for r in results:
        if r.status != "hit":
            continue
        if r.provider == "VirusTotal":
            sid = "VT_MALICIOUS_MANY" if r.malicious >= 3 else "VT_MALICIOUS_FEW"
        else:
            sid = "FEED_HIT"
        signals.append(make(sid, f"{r.provider}: {r.detail}.", "reputation", target))
    clean = [r for r in results if r.status == "clean"]
    if len(clean) >= 2 and not signals:
        signals.append(make("REPUTATION_CLEAN", f"Not listed by {', '.join(r.provider for r in clean)}.", "reputation", target))
    return signals
