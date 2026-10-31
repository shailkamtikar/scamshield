"""
URL extraction, canonicalisation and Unicode-deception analysis.

Everything here is pure string work: no network access.
"""

import ipaddress
import re
import unicodedata
from dataclasses import dataclass, field
from urllib.parse import urlsplit

import tldextract
from confusable_homoglyphs import confusables

_extractor = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)

INVISIBLE_CHARS = {
    "​", "‌", "‍", "⁠", "﻿", "­", "‎",
    "‏", "‪", "‫", "‬", "‭", "‮", "⁦",
    "⁧", "⁨", "⁩",
}

_URL_WITH_SCHEME = re.compile(
    r"(?i)\b(?:https?|hxxps?|ftp)://[^\s<>\"'`​]+"
)
_SCHEMELESS = re.compile(
    r"(?i)(?<![\w@./:\\-])"
    r"(?:[a-z0-9¡-￿](?:[a-z0-9¡-￿-]{0,61}[a-z0-9¡-￿])?\.)+"
    r"[a-z¡-￿]{2,24}"
    r"(?::\d{2,5})?(?:/[^\s<>\"'`]*)?"
)
_IP_URL = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?::\d{2,5})?(?:/[^\s<>\"'`]*)?")

_TRAILING = ".,!?;:'\")]}>*"


@dataclass
class ParsedUrl:
    original: str
    url: str
    scheme: str
    host: str  # unicode form, lowercase, no www.
    host_ascii: str  # IDNA/punycode form
    registrable: str
    subdomain: str
    suffix: str
    domain_label: str  # second-level label, e.g. "sbi" in sbi.co.in
    path: str
    query: str
    port: int | None
    is_ip: bool = False
    has_scheme: bool = True
    userinfo: str | None = None
    flags: set = field(default_factory=set)
    key: str = ""

    @property
    def display(self) -> str:
        return self.url


def refang(text: str) -> str:
    """Undo common 'defanging' so evil[.]com and hxxps:// are analysed."""
    out = re.sub(r"(?i)\bhxxp", "http", text)
    out = re.sub(r"(?i)\bfxp", "ftp", out)
    out = re.sub(r"\[\s*\.\s*\]|\(\s*\.\s*\)|\[\s*dot\s*\]|\(\s*dot\s*\)", ".", out, flags=re.I)
    out = re.sub(r"\[\s*:\s*\]", ":", out)
    out = re.sub(r"\[\s*://\s*\]", "://", out)
    return out


def _strip(candidate: str) -> str:
    while candidate and candidate[-1] in _TRAILING:
        # keep a closing paren that balances an opening one inside the URL
        if candidate[-1] == ")" and candidate.count("(") >= candidate.count(")"):
            break
        candidate = candidate[:-1]
    return candidate


def _scripts(label: str) -> set[str]:
    scripts = set()
    for ch in label:
        if ch.isascii():
            if ch.isalpha():
                scripts.add("LATIN")
            continue
        try:
            name = unicodedata.name(ch)
        except ValueError:
            scripts.add("UNKNOWN")
            continue
        scripts.add(name.split(" ")[0])
    return scripts


def _to_ascii(host: str) -> str:
    try:
        return host.encode("idna").decode("ascii")
    except UnicodeError:
        return host


def _to_unicode(host: str) -> str:
    try:
        return host.encode("ascii").decode("idna")
    except UnicodeError:
        return host


def parse_url(raw: str) -> ParsedUrl | None:
    """Parse a URL-ish string into a ParsedUrl, or None if it is not a URL."""

    original = raw
    candidate = refang(raw.strip())
    flags: set[str] = set()

    if any(ch in candidate for ch in INVISIBLE_CHARS):
        flags.add("INVISIBLE_CHARS")
        candidate = "".join(ch for ch in candidate if ch not in INVISIBLE_CHARS)

    has_scheme = bool(re.match(r"(?i)^[a-z][a-z0-9+.-]*://", candidate))
    to_split = candidate if has_scheme else "https://" + candidate
    try:
        parts = urlsplit(to_split)
        port = parts.port
    except ValueError:
        return None

    host = (parts.hostname or "").lower().strip(".")
    if not host:
        return None

    if parts.username or parts.password:
        flags.add("USERINFO_TRICK")
    scheme = parts.scheme.lower() if has_scheme else "https"
    if scheme not in {"http", "https", "ftp"}:
        return None

    is_ip = False
    try:
        ipaddress.ip_address(host)
        is_ip = True
    except ValueError:
        # decimal/hex/octal encoded IPv4 (e.g. http://3232235777/)
        if re.fullmatch(r"\d{8,10}|0x[0-9a-f]+", host):
            is_ip = True
            flags.add("OBFUSCATED_IP")

    if host.startswith("xn--") or ".xn--" in host:
        flags.add("PUNYCODE")
        host_unicode = _to_unicode(host)
    else:
        host_unicode = host

    if not host_unicode.isascii():
        flags.add("NON_ASCII_HOST")
        for label in host_unicode.split("."):
            if len(_scripts(label)) > 1:
                flags.add("MIXED_SCRIPT")
            if label and not label.isascii():
                try:
                    if confusables.is_dangerous(label):
                        flags.add("CONFUSABLE_CHARS")
                except Exception:
                    pass
        host_ascii = _to_ascii(host_unicode)
    else:
        host_ascii = host_unicode

    if host_unicode.startswith("www."):
        host_unicode = host_unicode[4:]
        host_ascii = host_ascii[4:] if host_ascii.startswith("www.") else host_ascii

    if is_ip:
        registrable, subdomain, suffix, domain_label = host_ascii, "", "", host_ascii
    else:
        ext = _extractor(host_ascii)
        if not ext.suffix:
            return None
        registrable = ext.top_domain_under_public_suffix
        subdomain, suffix, domain_label = ext.subdomain, ext.suffix, ext.domain
        if not registrable:
            return None

    if ":" in parts.netloc and parts.netloc.count(":") > 1 and not is_ip:
        pass

    normalized_scheme = scheme
    path = parts.path or ""
    key = f"{host_ascii}{path.rstrip('/')}"
    url = f"{normalized_scheme}://{parts.netloc.split('@')[-1]}{path}"
    if parts.query:
        url += f"?{parts.query}"

    return ParsedUrl(
        original=original,
        url=url,
        scheme=scheme,
        host=host_unicode,
        host_ascii=host_ascii,
        registrable=registrable,
        subdomain=subdomain,
        suffix=suffix,
        domain_label=domain_label,
        path=path,
        query=parts.query,
        port=port,
        is_ip=is_ip,
        has_scheme=has_scheme,
        userinfo=parts.username,
        flags=flags,
        key=key,
    )


def extract_urls(text: str, limit: int = 20) -> list[ParsedUrl]:
    """Find every URL in free text, including scheme-less ones, deduplicated."""

    cleaned = refang(text)
    found: list[tuple[int, str]] = []
    taken: list[tuple[int, int]] = []

    def overlaps(span):
        return any(s < span[1] and span[0] < e for s, e in taken)

    for pattern in (_URL_WITH_SCHEME, _SCHEMELESS, _IP_URL):
        for match in pattern.finditer(cleaned):
            span = match.span()
            if overlaps(span):
                continue
            candidate = _strip(match.group(0))
            if not candidate:
                continue
            # skip email domains (a@b.com) which the lookbehind may miss for unicode
            start = span[0]
            if start > 0 and cleaned[start - 1] == "@":
                continue
            taken.append((span[0], span[0] + len(candidate)))
            found.append((span[0], candidate))

    found.sort()
    results: list[ParsedUrl] = []
    seen: set[str] = set()
    for _, candidate in found:
        parsed = parse_url(candidate)
        if parsed is None:
            continue
        if parsed.key in seen:
            continue
        # A bare "word.tld" with a very short, common-looking suffix inside
        # normal prose (e.g. "file.py") is rejected by the PSL check above.
        seen.add(parsed.key)
        results.append(parsed)
        if len(results) >= limit:
            break
    return results
