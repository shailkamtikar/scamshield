"""
Static page inspection. Parses HTML TEXT only (no JavaScript is ever run)
looking for credential harvesting and brand impersonation.
"""

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urlsplit

from app.engine.signals import Signal, make
from app.intel.trust import GENERIC_BRAND_WORDS, brand_tokens
from app.intel.urls import ParsedUrl, parse_url


@dataclass
class PageInfo:
    title: str = ""
    text: str = ""
    forms: list = field(default_factory=list)  # {"action": str, "inputs": [types]}
    apk_links: int = 0
    iframes: int = 0
    meta_refresh: str = ""


class _Extractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.info = PageInfo()
        self._in_title = False
        self._skip = 0
        self._form = None
        self._text: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag in {"script", "style", "noscript"}:
            self._skip += 1
        elif tag == "form":
            self._form = {"action": a.get("action") or "", "inputs": []}
            self.info.forms.append(self._form)
        elif tag == "input" and self._form is not None:
            self._form["inputs"].append(((a.get("type") or "text").lower(), (a.get("name") or "").lower(), (a.get("placeholder") or "").lower()))
        elif tag == "iframe":
            self.info.iframes += 1
        elif tag == "a" and (a.get("href") or "").lower().split("?")[0].endswith(".apk"):
            self.info.apk_links += 1
        elif tag == "meta" and (a.get("http-equiv") or "").lower() == "refresh":
            self.info.meta_refresh = a.get("content") or ""

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag in {"script", "style", "noscript"} and self._skip:
            self._skip -= 1
        elif tag == "form":
            self._form = None

    def handle_data(self, data):
        if self._in_title:
            self.info.title += data
        elif not self._skip:
            self._text.append(data)

    def close(self):
        super().close()
        self.info.text = re.sub(r"\s+", " ", " ".join(self._text)).strip()[:4000]


def parse_html(html: str) -> PageInfo:
    parser = _Extractor()
    try:
        parser.feed(html)
        parser.close()
    except Exception:  # noqa: BLE001
        pass
    return parser.info


_SENSITIVE = re.compile(r"pass|otp|pin|cvv|card|aadhaar|aadhar|pan|upi|account|ifsc|netbank|mpin|debit|credit", re.I)


def analyze(parsed: ParsedUrl, html: str, final_host: str | None = None) -> list[Signal]:
    info = parse_html(html)
    t = parsed.key
    signals: list[Signal] = []

    def add(sid, detail):
        signals.append(make(sid, detail, "page", t))

    sensitive_forms = [
        f for f in info.forms
        if any(kind == "password" or _SENSITIVE.search(name) or _SENSITIVE.search(ph) for kind, name, ph in f["inputs"])
    ]
    if sensitive_forms:
        add("LOGIN_FORM_UNTRUSTED", "The page asks for a password, OTP or card/bank details.")
        base = final_host or parsed.host_ascii
        for f in sensitive_forms:
            action = f["action"]
            if action.startswith(("http://", "https://", "//")):
                target = parse_url(action if "://" in action else "https:" + action)
                if target and target.registrable != parse_url(f"https://{base}").registrable:
                    add("FORM_CROSS_DOMAIN", f"The form sends your data to a different site ({target.host_ascii}).")
                    break

    haystack = f"{info.title} {info.text[:1500]}".lower()
    tokens = brand_tokens()
    for token, brand in tokens.items():
        if len(token) < 4 or token in GENERIC_BRAND_WORDS:
            continue
        if re.search(rf"\b{re.escape(token)}\b", haystack):
            own = {d.split('.')[0] for d in brand.domains}
            if parsed.domain_label not in own:
                if sensitive_forms or "login" in haystack or "sign in" in haystack:
                    add("BRAND_MISMATCH_PAGE", f"The page presents itself as {brand.name}, but it is hosted on {parsed.registrable}.")
                    break

    if info.apk_links:
        add("APK_DOWNLOAD", "The page offers an Android app file (.apk) for direct download.")
    if not info.text and not info.forms and len(html) < 400:
        add("PAGE_PARKED_OR_EMPTY", "The page is empty.")
    return signals
