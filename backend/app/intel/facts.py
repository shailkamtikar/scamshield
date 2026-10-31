"""Domain facts from RDAP (registration age). Fails soft."""

import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from app.engine.signals import Signal, make
from app.intel.urls import ParsedUrl

_cache: dict[str, tuple[float, "DomainFacts"]] = {}
_lock = threading.Lock()


@dataclass
class DomainFacts:
    status: str  # ok | unavailable
    created: datetime | None = None
    age_days: int | None = None
    registrar: str | None = None


def lookup(registrable: str) -> DomainFacts:
    with _lock:
        item = _cache.get(registrable)
    if item and time.time() - item[0] < 24 * 3600:
        return item[1]

    try:
        with httpx.Client(timeout=httpx.Timeout(4.0, connect=3.0), follow_redirects=True) as c:
            r = c.get(f"https://rdap.org/domain/{registrable}", headers={"Accept": "application/rdap+json"})
        if r.status_code == 404:
            facts = DomainFacts("unavailable")
        else:
            r.raise_for_status()
            data = r.json()
            created = None
            for event in data.get("events", []):
                if event.get("eventAction") == "registration":
                    created = datetime.fromisoformat(event["eventDate"].replace("Z", "+00:00"))
                    break
            registrar = None
            for entity in data.get("entities", []):
                if "registrar" in entity.get("roles", []):
                    for item_ in entity.get("vcardArray", [None, []])[1]:
                        if item_[0] == "fn":
                            registrar = item_[3]
            age = None
            if created:
                if created.tzinfo is None:
                    created = created.replace(tzinfo=timezone.utc)
                age = (datetime.now(timezone.utc) - created).days
            facts = DomainFacts("ok" if created else "unavailable", created, age, registrar)
    except Exception:  # noqa: BLE001
        facts = DomainFacts("unavailable")

    if facts.status == "ok":
        with _lock:
            _cache[registrable] = (time.time(), facts)
    return facts


def to_signals(parsed: ParsedUrl, facts: DomainFacts) -> list[Signal]:
    if facts.status != "ok" or facts.age_days is None:
        return []
    t = parsed.key
    age = facts.age_days
    if age < 30:
        return [make("DOMAIN_AGE_LT_30D", f"{parsed.registrable} was registered only {age} day(s) ago.", "domain_facts", t)]
    if age < 365:
        return [make("DOMAIN_AGE_LT_1Y", f"{parsed.registrable} was registered {age // 30} month(s) ago.", "domain_facts", t)]
    if age > 5 * 365:
        return [make("DOMAIN_AGE_GT_5Y", f"{parsed.registrable} has existed for {age // 365} years.", "domain_facts", t)]
    return []
