"""Analyse ONE link end to end and return a structured report."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from app.config import settings
from app.engine import verdict as V
from app.engine.signals import Signal, make
from app.intel import facts, lexical, net, page, reputation, trust
from app.intel.urls import ParsedUrl, parse_url


@dataclass
class UrlReport:
    original: str
    url: str
    final_url: str
    host: str
    registrable: str
    trust: dict
    verdict: str
    score: int | None
    risk_level: str
    confidence: float
    confidence_factors: dict
    rule: str
    signals: list[dict]
    reachability: dict | None
    reputation: list[dict]
    domain_age_days: int | None = None
    registrar: str | None = None
    destination: "UrlReport | None" = None
    checks: dict = field(default_factory=dict)
    risk_points: int = 0
    _signals: list[Signal] = field(default_factory=list, repr=False)

    def to_dict(self) -> dict:
        d = {k: v for k, v in self.__dict__.items() if not k.startswith("_") and k != "destination"}
        if self.destination:
            d["destination"] = self.destination.to_dict()
        return d


def analyze_url(
    parsed: ParsedUrl,
    network: bool | None = None,
    extra_brands: tuple[str, ...] = (),
    depth: int = 0,
    inspect_page: bool = True,
    expected_brands: tuple = (),
    risky_context: bool = False,
) -> UrlReport:
    network = settings.enable_network_intel if network is None else network
    info = trust.classify(parsed)
    signals: list[Signal] = lexical.analyze(parsed, info, extra_brands)
    t = parsed.key

    if info.tier == "OFFICIAL":
        signals.append(make("TRUSTED_OFFICIAL", f"{parsed.registrable} is the official domain of {info.brand}.", "trust", t))
    elif info.tier == "POPULAR":
        signals.append(make("TRUSTED_POPULAR", f"{parsed.registrable} is a well-known site (top {info.rank}).", "trust", t))

    if expected_brands and risky_context and info.tier == "UNKNOWN":
        owned = {d.lower() for b in expected_brands for d in b.domains}
        if parsed.registrable.lower() not in owned and not info.shortener:
            names = ", ".join(sorted({b.name for b in expected_brands})[:2])
            signals.append(make("BRAND_MISMATCH_LINK", f"The message talks about {names}, but the link goes to {parsed.registrable}.", "message", t))

    checks = {"lexical": "done", "trust": "done"}
    rep_results: list[reputation.RepResult] = []
    fetch_result: net.FetchResult | None = None
    domain_facts: facts.DomainFacts | None = None
    structural_fake = any(s.id in V.FAKE_IDS for s in signals)

    if network:
        need_fetch = info.tier != "OFFICIAL"
        need_facts = info.tier == "UNKNOWN" and not parsed.is_ip and not info.platform
        use_vt = info.tier == "UNKNOWN"
        with ThreadPoolExecutor(max_workers=3) as pool:
            f_rep = pool.submit(reputation.check_all, parsed, info.tier != "UNKNOWN", use_vt)
            f_fetch = pool.submit(net.fetch, parsed.url, settings.enable_page_inspection and inspect_page and info.tier == "UNKNOWN") if need_fetch else None
            f_facts = pool.submit(facts.lookup, parsed.registrable) if need_facts else None
            rep_results = f_rep.result()
            fetch_result = f_fetch.result() if f_fetch else None
            domain_facts = f_facts.result() if f_facts else None

        signals.extend(reputation.to_signals(parsed, rep_results))
        by_name = {r.provider: r for r in rep_results}
        for key, provider in (("google_safe_browsing", "Google Safe Browsing"), ("openphish", "OpenPhish"), ("urlhaus", "URLhaus"), ("virustotal", "VirusTotal")):
            r = by_name.get(provider)
            if r is None:
                checks[key] = "skipped"  # not applicable for this trust tier
            elif r.status in {"hit", "clean"}:
                checks[key] = "done"
            else:
                checks[key] = "unavailable"  # no key, quota, outage

        if fetch_result is not None:
            checks["reachability"] = "done" if fetch_result.outcome not in {"ERROR", "BLOCKED"} else "unavailable"
            if fetch_result.outcome == "TLS_ERROR":
                signals.append(make("CERT_MISMATCH", "The site's security certificate is invalid.", "net", t))
            if len(fetch_result.chain) > 3:
                signals.append(make("REDIRECT_CHAIN_LONG", f"The link passes through {len(fetch_result.chain) - 1} redirects.", "net", t))
            if fetch_result.outcome == "OK" and fetch_result.body and info.tier == "UNKNOWN" and settings.enable_page_inspection:
                signals.extend(page.analyze(parsed, fetch_result.body))
                checks["page"] = "done"
            else:
                checks["page"] = "skipped"
        else:
            checks["reachability"] = "skipped"
            checks["page"] = "skipped"

        if need_facts:
            if domain_facts and domain_facts.status == "ok":
                checks["domain_age"] = "done"
                signals.extend(facts.to_signals(parsed, domain_facts))
            else:
                checks["domain_age"] = "unavailable"
        else:
            checks["domain_age"] = "skipped"
    else:
        for key in ("google_safe_browsing", "openphish", "urlhaus", "virustotal", "reachability", "domain_age", "page"):
            checks[key] = "unavailable" if key in {"google_safe_browsing", "openphish", "reachability"} else "skipped"

    destination = None
    if fetch_result and fetch_result.reachable and depth == 0:
        final = parse_url(fetch_result.final_url)
        if final and final.registrable != parsed.registrable:
            sig_id = "SHORTENER" if info.shortener else "REDIRECT_TO_OTHER_DOMAIN"
            if not any(s.id == sig_id for s in signals):
                signals.append(make(sig_id, f"The link redirects to {final.host_ascii}.", "net", t))
            destination = analyze_url(final, network=network, extra_brands=extra_brands, depth=1, inspect_page=True, expected_brands=expected_brands, risky_context=risky_context)

    tier = info.tier
    outcome = fetch_result.outcome if fetch_result else None
    if destination:
        for s in destination._signals:
            if s.polarity == "risk" and not any(x.id == s.id and x.target == t for x in signals):
                signals.append(make(s.id, s.explanation, s.source, t))
        tier = destination.trust["tier"] if destination.trust["tier"] != "OFFICIAL" or info.tier == "OFFICIAL" else "POPULAR"
        outcome = "OK"
        if info.shortener and destination.trust["tier"] in {"OFFICIAL", "POPULAR"}:
            signals.append(make("TRUSTED_POPULAR" if destination.trust["tier"] == "POPULAR" else "TRUSTED_OFFICIAL",
                                f"The link leads to {destination.registrable}.", "trust", t))

    assessment = V.assess_url(signals, tier, outcome, platform=bool(info.platform) and not destination)
    confidence, factors = V.confidence_for(assessment.verdict, assessment.signals, checks, tier)

    report = UrlReport(
        original=parsed.original,
        url=parsed.url,
        final_url=fetch_result.final_url if fetch_result else parsed.url,
        host=parsed.host_ascii,
        registrable=parsed.registrable,
        trust={"tier": info.tier, "brand": info.brand, "category": info.category, "rank": info.rank, "reason": info.reason, "platform": info.platform},
        verdict=assessment.verdict,
        score=assessment.score,
        risk_level=V.risk_level_for(assessment.verdict, assessment.score),
        confidence=confidence,
        confidence_factors=factors,
        rule=assessment.rule,
        signals=[s.to_dict() for s in assessment.signals],
        reachability=(
            {"outcome": fetch_result.outcome, "status": fetch_result.status, "chain": fetch_result.chain, "detail": fetch_result.detail}
            if fetch_result else None
        ),
        reputation=[{"provider": r.provider, "status": r.status, "detail": r.detail} for r in rep_results],
        domain_age_days=domain_facts.age_days if domain_facts else None,
        registrar=domain_facts.registrar if domain_facts else None,
        destination=destination,
        checks=checks,
        risk_points=assessment.risk_points,
        _signals=assessment.signals,
    )
    return report
