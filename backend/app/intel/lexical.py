"""
Offline lexical analysis of a URL: gibberish names, brand lookalikes,
combosquatting and structural oddities. No network access.
"""

import json
import math
import re
from functools import lru_cache
from pathlib import Path

from rapidfuzz.fuzz import ratio

from app.engine.signals import Signal, make
from app.intel.registry_data import ADMIN_WORDS, RISKY_TLDS
from app.intel.trust import GENERIC_BRAND_WORDS, TrustInfo, brand_tokens
from app.intel.urls import ParsedUrl

DATA = Path(__file__).parent / "data"
_LEET = {"0": "o", "1": "l", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"}


@lru_cache(maxsize=1)
def _model():
    path = DATA / "lexical_model.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def gibberish_score(word: str) -> float | None:
    """Mean per-character log-probability of `word` under a model trained on
    real domain names. Lower = less natural. None if no model is available."""

    model = _model()
    if model is None:
        return None
    table, default, vocab = model["model"], model["default"], model["vocab"]
    padded = "^^" + word + "$"
    total, n = 0.0, 0
    for i in range(2, len(padded)):
        ctx, ch = padded[i - 2 : i], padded[i]
        row = table.get(ctx)
        if row is None:
            total += math.log(0.1 / (0.1 * vocab + 1))
        else:
            total += row.get(ch, default[ctx])
        n += 1
    return total / max(n, 1)


def is_gibberish(word: str) -> bool:
    if len(word) < 6:
        return False
    if re.fullmatch(r"[a-f0-9]{12,}", word):
        return True
    score = gibberish_score(word)
    model = _model()
    return score is not None and model is not None and score < model["threshold"]


def _words(text: str) -> list[str]:
    return [w for w in re.split(r"[^a-z0-9]+", text.lower()) if w]


def _deleet_variants(word: str) -> set[str]:
    base = "".join(_LEET.get(c, c) for c in word)
    variants = {base, base.replace("rn", "m"), base.replace("vv", "w")}
    if "1" in word:
        variants.add("".join("i" if c == "1" else _LEET.get(c, c) for c in word))
    return variants


def _match_brand(word: str, tokens: dict, allow_substring: bool = True):
    """Return (brand, kind) where kind is 'exact', 'embedded' or 'lookalike'."""

    if word in tokens:
        return tokens[word], "exact"

    if allow_substring:
        for token, brand in tokens.items():
            if len(token) >= 5 and token not in GENERIC_BRAND_WORDS and token in word and word != token:
                rest = word.replace(token, "", 1)
                # only when what is glued on is an account/security word or digits
                if rest in ADMIN_WORDS or rest.isdigit() or rest in {"india", "bharat", "official", "app", "bank", "online"}:
                    return brand, "embedded"

    for variant in _deleet_variants(word):
        if variant != word and variant in tokens and len(variant) >= 4:
            return tokens[variant], "lookalike"

    if len(word) >= 6:
        for token, brand in tokens.items():
            if len(token) >= 6 and len(word) >= 6 and abs(len(token) - len(word)) <= 2 and word != token and token not in GENERIC_BRAND_WORDS:
                if ratio(word, token) >= 85:
                    return brand, "lookalike"
    return None, None


def analyze(parsed: ParsedUrl, trust: TrustInfo, extra_brands: tuple[str, ...] = ()) -> list[Signal]:
    signals: list[Signal] = []
    target = parsed.key
    src = "lexical"

    def add(signal_id: str, detail: str):
        signals.append(make(signal_id, detail, src, target))

    host = parsed.host

    # ---- Unicode / structure flags (always evaluated) ----
    if "INVISIBLE_CHARS" in parsed.flags:
        add("INVISIBLE_CHARS", "The link contains invisible characters designed to hide its real address.")
    if "USERINFO_TRICK" in parsed.flags:
        add("USERINFO_TRICK", f"The text before '@' is a decoy; the link really goes to {parsed.host_ascii}.")
    if parsed.flags & {"MIXED_SCRIPT", "CONFUSABLE_CHARS"}:
        add("HOMOGRAPH", f"'{host}' mixes look-alike characters from different alphabets.")
    elif "PUNYCODE" in parsed.flags or "NON_ASCII_HOST" in parsed.flags:
        add("PUNYCODE", f"'{parsed.host_ascii}' is an internationalised domain name.")
    if "OBFUSCATED_IP" in parsed.flags:
        add("OBFUSCATED_IP", f"'{parsed.host_ascii}' is an IP address written in an encoded form.")
    elif parsed.is_ip:
        add("RAW_IP", f"The link points to the raw IP address {parsed.host_ascii} instead of a domain name.")

    if trust.tier == "OFFICIAL":
        return signals

    if re.search(r"\.(exe|apk|msi|bat|scr|jar|ps1|vbs|lnk|iso|dmg|sh|bin|zip|rar|7z|cmd|hta|dll)$", parsed.path.lower()):
        add("RISKY_FILE_LINK", f"The link downloads a file ({parsed.path.rsplit('/', 1)[-1]}) rather than showing a web page.")

    if parsed.scheme == "http" and parsed.has_scheme:
        add("NO_HTTPS", "The link does not use HTTPS.")
    if trust.shortener:
        add("SHORTENER", f"{parsed.host_ascii} is a link shortener; the real destination is hidden.")
    if trust.platform:
        add("USER_CONTENT_HOST", f"The page is hosted on {trust.platform}, where anyone can publish content.")

    if parsed.is_ip:
        return signals

    sub_labels = [s for s in parsed.subdomain.split(".") if s]
    if len(sub_labels) >= 3:
        add("DEEP_SUBDOMAINS", f"The address has {len(sub_labels)} subdomain levels.")
    if len(parsed.host_ascii) > 45:
        add("LONG_HOSTNAME", "The hostname is unusually long.")
    if parsed.suffix.split(".")[-1] in RISKY_TLDS:
        add("RISKY_TLD", f"'.{parsed.suffix}' domains are frequently abused by scammers.")
    if parsed.domain_label.removeprefix("xn--").count("-") >= 3:
        add("MANY_HYPHENS", "The domain name contains many hyphens.")

    if trust.tier == "POPULAR":
        return signals

    tokens = dict(brand_tokens())
    for extra in extra_brands:
        squashed = re.sub(r"[^a-z0-9]", "", extra.lower())
        if len(squashed) >= 3:
            tokens.setdefault(squashed, type("B", (), {"name": extra, "category": "claimed", "domains": ()})())

    label_words = [] if trust.platform else _words(parsed.domain_label)
    sub_words = [w for label in sub_labels for w in _words(label)]
    path_words = _words(parsed.path)[:12]

    # ---- gibberish ----
    gib_words = [w for w in label_words if is_gibberish(w)] if not trust.platform else []
    gib_sub = [w for w in sub_words if is_gibberish(w)]
    if gib_words:
        add("DOMAIN_GIBBERISH", f"'{parsed.domain_label}' looks like a random string, not a real name.")
    elif gib_sub:
        add("DOMAIN_GIBBERISH", f"The address part '{parsed.subdomain}' looks randomly generated.")

    # ---- brand analysis ----
    admin_in_label = [w for w in label_words if w in ADMIN_WORDS]
    brand_found = None
    for word in label_words:
        brand, kind = _match_brand(word, tokens, allow_substring=not trust.platform)
        if brand is None:
            continue
        # A generic English word is only a brand when it stands alone as a lookalike target.
        if kind in {"embedded"} and word in GENERIC_BRAND_WORDS:
            continue
        brand_found = (brand, kind, word)
        break

    if brand_found:
        brand, kind, word = brand_found
        if kind == "lookalike":
            add("BRAND_LOOKALIKE", f"'{parsed.domain_label}' imitates {brand.name} but is not a {brand.name} domain.")
        elif admin_in_label:
            add("BRAND_COMBOSQUAT", f"'{parsed.domain_label}' combines {brand.name} with '{admin_in_label[0]}', a common phishing pattern.")
        elif len(label_words) > 1 or kind == "embedded":
            add("BRAND_IN_DOMAIN", f"'{parsed.domain_label}' contains the {brand.name} name but is not a {brand.name} domain.")
        elif word in tokens and tokens[word].name and word not in GENERIC_BRAND_WORDS and len(word) >= 5:
            # e.g. "paytm.xyz": brand label on a foreign suffix
            add("BRAND_IN_DOMAIN", f"'{parsed.registrable}' uses the {brand.name} name but is not a {brand.name} domain.")
    else:
        if admin_in_label and (len(label_words) >= 2 or "-" in parsed.domain_label):
            add("ADMIN_COMPOUND", f"'{parsed.domain_label}' is built from account/security words ({', '.join(admin_in_label[:3])}).")

    # brand name hiding in subdomain / path of someone else's domain
    if not brand_found or brand_found[1] != "lookalike":
        scan_words = sub_words + path_words
        for word in scan_words:
            brand, kind = _match_brand(word, tokens, allow_substring=False)
            if brand is not None and word not in GENERIC_BRAND_WORDS and (len(word) >= 3 or word == 'fb'):
                where = "address" if word in sub_words else "page path"
                add("BRAND_IN_SUBDOMAIN_OR_PATH", f"The {where} mentions '{word}' ({brand.name}) but the site is {parsed.registrable}.")
                break

    return signals
