"""
Trust knowledge: which domains are verified official, which are merely
popular, and which are free hosting platforms where anyone can publish.
"""

import gzip
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import tldextract

from app.intel.registry_data import REGISTRY, URL_SHORTENERS, USER_CONTENT_PLATFORMS
from app.intel.urls import ParsedUrl

DATA = Path(__file__).parent / "data"
_extractor = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)

# Registrable-suffix rules: anything under these is run by governments or
# accredited institutions (registration is restricted).
OFFICIAL_SUFFIXES = {
    "gov.in", "nic.in", "ac.in", "edu.in", "res.in", "mil.in", "gov", "edu",
    "mil", "gov.uk", "ac.uk", "gov.au", "edu.au", "gc.ca", "bank.in", "fin.in", "sbi",
}


# Official domains that still let anyone create a link or page on them, so they say nothing about who sent the message.
OPEN_LINK_SERVICES = {"t.me", "telegram.me", "wa.me", "discord.gg", "forms.gle", "ig.me", "fb.me", "lnkd.in", "youtu.be"}

ZONE_NAMES = {
    "bank.in": "a licensed Indian bank (restricted .bank.in domain)",
    "fin.in": "a regulated Indian financial institution (restricted .fin.in domain)",
    "gov.in": "the Government of India", "nic.in": "the Government of India", "mil.in": "the Indian armed forces",
    "ac.in": "an Indian academic institution", "edu.in": "an Indian academic institution", "res.in": "an Indian research institution",
}


@dataclass(frozen=True)
class Brand:
    name: str
    category: str
    domains: tuple[str, ...]


@dataclass
class TrustInfo:
    tier: str  # OFFICIAL | POPULAR | UNKNOWN
    brand: str | None = None
    category: str | None = None
    zone: str | None = None  # restricted zone the host sits in, e.g. "bank.in"
    rank: int | None = None
    platform: str | None = None  # user-content platform the host sits on
    shortener: bool = False
    reason: str = ""


@lru_cache(maxsize=1)
def _brands() -> list[Brand]:
    out = []
    for category, entries in REGISTRY.items():
        for name, domains in entries:
            out.append(Brand(name, category, tuple(domains)))
    return out


@lru_cache(maxsize=1)
def official_index() -> dict[str, Brand]:
    index: dict[str, Brand] = {}
    for brand in _brands():
        for domain in brand.domains:
            index.setdefault(domain.lower(), brand)
    return index


@lru_cache(maxsize=1)
def tranco_ranks() -> dict[str, int]:
    path = DATA / "tranco_top.txt.gz"
    ranks: dict[str, int] = {}
    if path.exists():
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for i, line in enumerate(fh, start=1):
                ranks[line.strip()] = i
    return ranks


def _squash(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


@lru_cache(maxsize=1)
def brand_tokens() -> dict[str, Brand]:
    """token -> brand. Used for lookalike / brand-in-domain detection."""
    tokens: dict[str, Brand] = {}
    for brand in _brands():
        candidates = {_squash(brand.name)}
        for part in re.split(r"[/&]", brand.name):
            candidates.add(_squash(part))
        for domain in brand.domains:
            label = _extractor(domain).domain  # "google" for mail.google.com, not "mail"
            candidates.add(_squash(label))
        for token in candidates:
            if len(token) >= 3 and token not in tokens:
                tokens[token] = brand
    for extra_token, brand_name in (('fb', 'Facebook'),):
        for brand in _brands():
            if brand.name == brand_name:
                tokens.setdefault(extra_token, brand)
    # Short/ambiguous words that are also common English words are only
    # treated as brands when they are an exact registrable label (handled in
    # lexical.py via GENERIC_BRAND_WORDS).
    return tokens


GENERIC_BRAND_WORDS = {
    "mail", "pay", "play", "docs", "drive", "maps", "open", "music", "one", "go", "app", "web", "live", "news", "life",
    "bank", "money", "cash", "card", "home", "shop", "store", "online", "direct", "invest", "trade", "secure",
    "apple", "signal", "meta", "target", "zoom", "wise", "kite", "cred", "ola",
    "oyo", "mi", "x", "visa", "amazon", "indeed", "monster", "discord", "slack",
    "notion", "canva", "reddit", "twitch", "booking", "oracle", "intel", "wynk",
    "gaana", "voot", "nic", "sc", "citi", "ups", "dhl", "bse", "nse", "lic",
    "cleartax", "gati", "ajio", "hp", "pan", "uber", "meesho", "swiggy",
    "office", "windows", "outlook", "teams", "edge", "word", "excel", "bing", "azure", "access", "gold", "prime", "neu",
}


def platform_of(host: str) -> str | None:
    host = host.lower()
    for platform in USER_CONTENT_PLATFORMS:
        if host == platform or host.endswith("." + platform):
            return platform
    return None


def is_shortener(host: str) -> bool:
    return host.lower() in URL_SHORTENERS or host.lower().removeprefix("www.") in URL_SHORTENERS


def classify(parsed: ParsedUrl) -> TrustInfo:
    """Decide trust tier for a parsed URL (offline, no network)."""

    shortener = is_shortener(parsed.host_ascii)
    platform = platform_of(parsed.host_ascii)

    # Platform pages (github.io, pages.dev, drive.google.com ...) prove nothing
    # about the content, so they are never auto-trusted.
    if platform and platform not in {"docs.google.com", "drive.google.com", "dropbox.com", "medium.com", "wordpress.com"}:
        return TrustInfo("UNKNOWN", platform=platform, shortener=shortener, reason="free hosting platform")
    if platform:
        return TrustInfo("UNKNOWN", platform=platform, shortener=shortener, reason="user-shared content on a major platform")

    if parsed.is_ip:
        return TrustInfo("UNKNOWN", shortener=False, reason="raw IP")

    index = official_index()
    registrable = parsed.registrable.lower()
    host = parsed.host_ascii.lower()

    brand = index.get(registrable) or index.get(host)
    if brand:
        return TrustInfo("OFFICIAL", brand=brand.name, category=brand.category, shortener=shortener, reason=f"official {brand.name} domain")

    # Judge the whole host: "hdfc.bank.in" is an ordinary subdomain of the restricted bank.in zone, so the
    # registrable part alone ("bank.in") would hide that every name under it was approved for a bank.
    if parsed.suffix.lower() in OFFICIAL_SUFFIXES or any(host == s or host.endswith("." + s) for s in OFFICIAL_SUFFIXES):
        zone = next((s for s in sorted(OFFICIAL_SUFFIXES, key=len, reverse=True) if host == s or host.endswith("." + s)), parsed.suffix.lower())
        name = ZONE_NAMES.get(zone, "a government or academic institution")
        category = "bank" if zone in {"bank.in", "fin.in"} else "government"
        return TrustInfo("OFFICIAL", brand=name, category=category, zone=zone, shortener=shortener, reason=f".{zone} is a restricted domain: only {name} can register under it")

    rank = tranco_ranks().get(registrable)
    if rank:
        return TrustInfo("POPULAR", rank=rank, shortener=shortener, reason=f"top-{rank} most visited site")

    return TrustInfo("UNKNOWN", shortener=shortener, reason="not on any trusted list")
