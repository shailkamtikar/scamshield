"""
Static page inspection. Parses HTML TEXT only (no JavaScript is ever run).

Calibrated on real pages (see scripts/collect_pages.py and
scripts/tune_pages.py): an ordinary login form proves nothing, so the strong
signals require a password/card form on a page that presents itself as a
brand it does not belong to, or a hosting provider's own phishing warning.
"""

import re
from dataclasses import asdict, dataclass, field
from html.parser import HTMLParser

from app.engine.signals import Signal, make
from app.intel.trust import GENERIC_BRAND_WORDS, brand_tokens
from app.intel.urls import ParsedUrl, parse_url


@dataclass
class PageInfo:
    title: str = ""
    text: str = ""
    forms: list = field(default_factory=list)  # {"action": str, "inputs": [(type, name, placeholder)]}
    apk_links: int = 0
    iframes: int = 0
    meta_refresh: str = ""
    scripts: int = 0
    html_len: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


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
            if tag == "script":
                self.info.scripts += 1
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
    parser.info.title = parser.info.title.strip()
    parser.info.html_len = len(html)
    return parser.info


_HOST_WARNING = re.compile(
    r"suspected (?:phishing|malware)|deceptive site ahead|reported phishing|this (?:site|page) has been (?:suspended|taken down|reported)|"
    r"phishing site (?:warning|detected)|warning: (?:suspected )?phishing",
    re.I,
)
_CREDENTIAL_NAME = re.compile(r"pass|passwd|pwd|otp|\bpin\b|mpin|cvv|cvc|card.?num|aadhaa?r|netbank", re.I)


def has_credential_form(info: PageInfo) -> bool:
    for form in info.forms:
        for item in form["inputs"]:
            kind, name, placeholder = item
            if kind == "password" or _CREDENTIAL_NAME.search(name) or _CREDENTIAL_NAME.search(placeholder):
                return True
    return False


def _title_brand(info: PageInfo, parsed: ParsedUrl):
    """A brand the page's TITLE claims to be, when the site is not that brand's."""
    title = info.title.lower()
    if not title:
        return None
    label = parsed.domain_label.lower()
    owned_check = parsed.registrable.lower()
    for token, brand in brand_tokens().items():
        if len(token) < 4 or token in GENERIC_BRAND_WORDS or token == label:
            continue
        spaced = brand.name.lower()
        if re.search(rf"{re.escape(token)}", title) or (len(spaced) >= 5 and spaced in title):
            if owned_check not in {d.lower() for d in brand.domains}:
                return brand
    return None


def analyze_info(parsed: ParsedUrl, info: PageInfo, final_host: str | None = None) -> list[Signal]:
    t = parsed.key
    signals: list[Signal] = []

    def add(sid, detail):
        signals.append(make(sid, detail, "page", t))

    if _HOST_WARNING.search(info.title) or (_HOST_WARNING.search(info.text[:300]) and len(info.text) < 800):
        add("HOST_FLAGGED_PAGE", "The hosting provider itself shows a phishing or malware warning on this page.")
        return signals

    credential = has_credential_form(info)
    brand = _title_brand(info, parsed)

    if credential and brand:
        add("BRAND_MISMATCH_PAGE", f"The page calls itself {brand.name} and asks for a password, but it is hosted on {parsed.registrable}.")
    elif brand:
        add("BRAND_MENTION_PAGE", f"The page title mentions {brand.name}, but the site is {parsed.registrable}.")
    elif credential:
        add("LOGIN_FORM_UNTRUSTED", "The page asks for a password or similar secret, and this site is not on any trusted list.")

    if credential:
        base = parse_url(f"https://{final_host or parsed.host_ascii}")
        for form in info.forms:
            has_secret = any(kind == "password" for kind, _, _ in form["inputs"])
            action = form["action"]
            if has_secret and action.startswith(("http://", "https://", "//")):
                target = parse_url(action if "://" in action else "https:" + action)
                if target and base and target.registrable != base.registrable:
                    add("FORM_CROSS_DOMAIN", f"The password form sends what you type to a different site ({target.host_ascii}).")
                    break

    if info.apk_links:
        add("APK_DOWNLOAD", "The page offers an Android app file (.apk) for direct download.")
    if not info.text and not info.forms and info.html_len < 400:
        add("PAGE_PARKED_OR_EMPTY", "The page is empty.")
    return signals


def analyze(parsed: ParsedUrl, html: str, final_host: str | None = None) -> list[Signal]:
    return analyze_info(parsed, parse_html(html), final_host)
