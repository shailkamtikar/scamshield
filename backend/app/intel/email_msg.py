"""
Raw e-mail (RFC 822 / .eml text) handling: sender, Reply-To, authentication results, attachments and hidden links.

Only what is actually in the pasted text is used. If the headers were not pasted, nothing here runs and the message is
judged on its words and links alone. Nothing is fetched and no attachment is opened: file names are judged by name only.

Authentication results are read from the receiving server's `Authentication-Results` header. They are evidence, not proof:
a pass does not make a message safe (accounts get compromised) and a failure can come from forwarding or mailing lists.
"""

import re
from dataclasses import dataclass, field
from email import message_from_string, policy
from email.utils import getaddresses
from html.parser import HTMLParser

import tldextract

from app.engine.signals import Signal, make
from app.intel import lexical
from app.intel.trust import GENERIC_BRAND_WORDS, brand_tokens, classify
from app.intel.urls import parse_url

_extractor = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)
MAX_CHARS = 200_000

FREE_MAIL = {"gmail.com", "yahoo.com", "yahoo.in", "outlook.com", "hotmail.com", "rediffmail.com", "proton.me", "protonmail.com", "icloud.com", "aol.com", "mail.com", "ymail.com"}
RISKY_EXT = {"exe", "scr", "com", "pif", "bat", "cmd", "ps1", "vbs", "vbe", "js", "jse", "wsf", "hta", "jar", "msi", "apk", "lnk", "iso", "img", "dll", "reg", "cpl", "msc"}
ODD_EXT = {"docm", "xlsm", "pptm", "html", "htm", "svg", "chm", "one", "zip", "rar", "7z"}  # legitimate sometimes, a common carrier often
# Mail-marketing and tracking services legitimately sit between a visible address and the real page.
TRACKERS = {
    "list-manage.com", "mailchimp.com", "sendgrid.net", "mandrillapp.com", "amazonses.com", "hubspotlinks.com", "hs-sites.com", "exacttarget.com", "sfmc-content.com",
    "mailgun.org", "sparkpostmail.com", "customeriomail.com", "klclick.com", "klaviyomail.com", "cmail19.com", "cmail20.com", "rs6.net", "mkt.com", "sailthru.com",
    "braze.com", "moengage.com", "clevertap-prod.com", "linkedin.com", "lnkd.in", "google.com", "bit.ly", "t.co", "page.link", "app.link", "onelink.me",
}
DOC_EXT = {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "jpg", "jpeg", "png", "csv", "rtf"}
BEC_WORDS = re.compile(r"\b(?:wire transfer|gift cards?|urgent(?:ly)? (?:payment|transfer)|change (?:of )?(?:bank|account) details|new bank account|invoice (?:is )?(?:overdue|attached)|are you (?:available|at your desk)|keep (?:this )?confidential)\b", re.I)
HEADER_START = re.compile(r"(?im)^(?:from|to|subject|date|received|return-path|reply-to|authentication-results|message-id|mime-version|content-type):")


@dataclass
class ParsedEmail:
    body_text: str
    from_name: str = ""
    from_addr: str = ""
    reply_to: str = ""
    return_path: str = ""
    subject: str = ""
    auth: dict = field(default_factory=dict)
    attachments: list = field(default_factory=list)
    anchors: list = field(default_factory=list)  # (visible text, href)
    signals: list[Signal] = field(default_factory=list)

    def summary(self) -> dict:
        return {
            "from_name": self.from_name,
            "from": self.from_addr,
            "reply_to": self.reply_to,
            "return_path": self.return_path,
            "subject": self.subject[:200],
            "authentication": self.auth,
            "attachments": self.attachments,
            "hidden_links": [{"shown": t, "goes_to": h} for t, h in self.anchors if _mismatch(t, h)][:8],
            "note": "Authentication results are evidence, not proof: a pass does not make a message safe and a failure can come from forwarding.",
        }


class _Html(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text: list[str] = []
        self.anchors: list[tuple[str, str]] = []
        self._href: str | None = None
        self._buf: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "head"}:
            self._skip += 1
        if tag == "a":
            self._href = dict(attrs).get("href") or ""
            self._buf = []
        if tag in {"br", "p", "div", "tr", "li"}:
            self.text.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style", "head"} and self._skip:
            self._skip -= 1
        if tag == "a" and self._href is not None:
            shown = " ".join("".join(self._buf).split())
            if self._href.startswith(("http://", "https://")):
                self.anchors.append((shown, self._href))
            self._href = None

    def handle_data(self, data):
        if self._skip:
            return
        self.text.append(data)
        if self._href is not None:
            self._buf.append(data)


def looks_like_email(text: str) -> bool:
    head = text[:4000]
    return len(HEADER_START.findall(head)) >= 3 and re.search(r"(?im)^from:", head) is not None


def _domain(addr: str) -> str:
    return addr.rsplit("@", 1)[-1].lower().strip(" <>") if "@" in addr else ""


def _registrable(host: str) -> str:
    ext = _extractor(host)
    return f"{ext.domain}.{ext.suffix}".lower() if ext.suffix else host.lower()


_DOMAIN_TEXT = re.compile(r"(?i)\b(?:https?://)?((?:[a-z0-9-]+\.)+[a-z]{2,})(?:/\S*)?")


def _mismatch(shown: str, href: str) -> bool:
    """The text of a link names one site and the link goes to another."""
    m = _DOMAIN_TEXT.search(shown or "")
    if not m:
        return False
    p = parse_url(href)
    if not p:
        return False
    reg = p.registrable.lower()
    if reg in TRACKERS or re.match(r"(?:click|clicks|links?|track|trk|email|em|go|url|redirect|news|r|t|e)\d*\.", p.host_ascii.lower()) and _registrable(m.group(1)) in p.host_ascii.lower():
        return False
    return _registrable(m.group(1)) != reg


def parse(text: str) -> ParsedEmail | None:
    if not looks_like_email(text):
        return None
    msg = message_from_string(text[:MAX_CHARS], policy=policy.default)

    name, addr = ("", "")
    pairs = getaddresses([str(msg.get("From", ""))])
    if pairs:
        name, addr = pairs[0]
    reply_pairs = getaddresses([str(msg.get("Reply-To", ""))])
    reply_to = reply_pairs[0][1] if reply_pairs else ""
    rpath = str(msg.get("Return-Path", "")).strip("<> ")

    body_parts: list[str] = []
    anchors: list[tuple[str, str]] = []
    attachments: list[dict] = []
    for part in msg.walk():
        if part.is_multipart():
            continue
        filename = part.get_filename()
        ctype = part.get_content_type()
        if filename:
            attachments.append({"name": filename[:120], "type": ctype})
            continue
        try:
            content = part.get_content()
        except Exception:  # noqa: BLE001
            continue
        if not isinstance(content, str):
            continue
        if ctype == "text/html":
            parser = _Html()
            parser.feed(content[:MAX_CHARS])
            body_parts.append("".join(parser.text))
            anchors.extend(parser.anchors)
        elif ctype == "text/plain":
            body_parts.append(content)
    body = "\n".join(p.strip() for p in body_parts if p.strip())
    # a plain text part and an HTML part usually repeat each other; keep the longer one
    if len(body_parts) == 2 and all(body_parts):
        body = max(body_parts, key=len).strip()

    auth_text = " ".join(str(h) for h in msg.get_all("Authentication-Results", [])) + " " + " ".join(str(h) for h in msg.get_all("Received-SPF", []))
    auth = {}
    for key in ("spf", "dkim", "dmarc"):
        m = re.search(rf"\b{key}=(\w+)", auth_text, re.I)
        if m:
            auth[key] = m.group(1).lower()

    email = ParsedEmail(
        body_text=body, from_name=name, from_addr=addr.lower(), reply_to=reply_to.lower(), return_path=rpath.lower(),
        subject=str(msg.get("Subject", "")), auth=auth, attachments=attachments, anchors=anchors,
    )
    email.signals = _signals(email)
    return email


def _signals(e: ParsedEmail) -> list[Signal]:
    out: list[Signal] = []
    sender_domain = _domain(e.from_addr)
    sender_reg = _registrable(sender_domain) if sender_domain else ""

    sender_url = parse_url("https://" + sender_domain) if sender_domain else None
    if sender_url is not None:
        info = classify(sender_url)
        lex = {s.id for s in lexical.analyze(sender_url, info)} if info.tier != "OFFICIAL" else set()
        if lex & {"BRAND_LOOKALIKE", "BRAND_COMBOSQUAT", "HOMOGRAPH"}:
            out.append(make("SENDER_LOOKALIKE", f"The sender's domain {sender_domain} imitates a known organisation.", "email"))
        else:
            # a brand named in the display name while the address belongs to someone else (a free mailbox, another company)
            low_name = re.sub(r"[^a-z0-9 ]", " ", e.from_name.lower())
            squashed = re.sub(r"[^a-z0-9]", "", sender_domain)
            for token, brand in brand_tokens().items():
                if len(token) < 3 or token in GENERIC_BRAND_WORDS or token in squashed:
                    continue
                if re.search(rf"\b{re.escape(token)}\b", low_name) and not (info.tier == "OFFICIAL" and info.brand == brand.name):
                    out.append(make("SENDER_DISPLAY_NAME_MISMATCH", f"The sender calls itself '{e.from_name.strip()}' but the address is {e.from_addr}, which is not {brand.name}'s.", "email"))
                    break

    if e.reply_to and sender_domain and _registrable(_domain(e.reply_to)) != sender_reg:
        out.append(make("REPLY_TO_MISMATCH", f"Replies go to {e.reply_to}, a different domain from the sender ({e.from_addr}).", "email"))

    if e.auth.get("dmarc") == "fail" or (e.auth.get("spf") in {"fail", "softfail"} and e.auth.get("dkim") == "fail"):
        out.append(make("AUTH_FAILED", "The receiving server could not authenticate the sender (this can also happen with forwarded mail).", "email"))

    for att in e.attachments:
        parts = att["name"].lower().rsplit(".", 2)
        ext = parts[-1] if len(parts) > 1 else ""
        double = len(parts) == 3 and parts[-2] in DOC_EXT and ext in RISKY_EXT
        if ext in RISKY_EXT or double:
            out.append(make("RISKY_ATTACHMENT", f"The attachment '{att['name']}' is a program or script type{' and hides its real type behind a document name' if double else ''}.", "email"))
            break
        if ext in ODD_EXT:
            out.append(make("SUSPICIOUS_ATTACHMENT", f"The attachment '{att['name']}' is a type often used to carry macros or fake pages.", "email"))

    for shown, href in e.anchors:
        if _mismatch(shown, href):
            out.append(make("LINK_TEXT_MISMATCH", f"A link shows '{shown[:50]}' but really goes to {_registrable(parse_url(href).host_ascii) if parse_url(href) else href[:40]}.", "email"))
            break

    if BEC_WORDS.search(e.body_text + " " + e.subject) and (_domain(e.reply_to) in FREE_MAIL or sender_domain in FREE_MAIL or any(s.id in {"REPLY_TO_MISMATCH", "SENDER_DISPLAY_NAME_MISMATCH"} for s in out)):
        out.append(make("BEC_PATTERN", "A payment or confidential request arrives from an address that does not match the person or company it claims to be.", "email"))
    return out


def body_with_links(e: ParsedEmail) -> str:
    """Body text plus every real link target, so the link checker sees what a click would open."""
    seen, extra = set(), []
    for _, href in e.anchors:
        if href not in seen:
            seen.add(href)
            extra.append(href)
    return e.body_text + ("\n\nLinks in this e-mail:\n" + "\n".join(extra[:12]) if extra else "")
