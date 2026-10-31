from rapidfuzz.fuzz import ratio


COMMON_DOMAIN_PREFIXES = {
    "www",
    "login",
    "secure",
    "account",
    "verify",
}


def _clean_hostname(domain: str) -> str:
    """Strip protocol, path/query, and a leading 'www.' from a URL or hostname."""

    cleaned = domain.lower().strip()
    cleaned = cleaned.replace("https://", "").replace("http://", "")
    cleaned = cleaned.split("/")[0]

    if cleaned.startswith("www."):
        cleaned = cleaned[4:]

    return cleaned


def normalize_domain(domain: str) -> str:
    """
    Extract the core brand-like token from a domain's first label, skipping
    a small set of generic words that are commonly glued onto lookalike
    domains (e.g. "miconsoft-login" -> "miconsoft", "login-microsoft" ->
    "microsoft"). This token is what similarity is measured against.
    """

    hostname = _clean_hostname(domain)
    first_label = hostname.split(".")[0]
    parts = first_label.split("-")

    for part in parts:
        if part not in COMMON_DOMAIN_PREFIXES:
            return part

    return parts[0]


# Generic, brand-agnostic vocabulary commonly glued onto an arbitrary
# token to fabricate a "this belongs to some official account/billing
# service" compound domain, e.g. "netflix-billing-support",
# "bank-account-verification". Contains no company/brand names — only
# generic security/administrative words — so structure detection below
# works without knowing (or requiring the user to supply) which brand,
# if any, is being impersonated.
COMBOSQUAT_ADMIN_WORDS = {
    "login", "signin", "secure", "security", "account", "verify",
    "verification", "confirm", "confirmation", "update", "billing",
    "payment", "support", "service", "alert", "suspended", "renew",
    "renewal", "invoice", "helpdesk", "customer", "password", "recovery",
    "authentication", "validate",
}


def has_combosquat_structure(domain: str) -> str | None:
    """
    Detect the STRUCTURAL shape of a combosquatting/lookalike domain — a
    hyphenated compound containing a generic administrative/security word
    — without a claimed organization to compare against.

    This exists because identity_verification_node's brand comparison
    (compare_domains, below) can only fire when a claimed_organization is
    known. A QR code (or any bare URL with no surrounding text) often
    carries no such context, so a domain like
    "netflix-billing-support.example" previously produced ZERO evidence
    when no brand was named — even though its shape alone is a classic
    lookalike pattern. This check is brand-agnostic: it fires the same
    way regardless of modality or whether a claimed organization was
    ever supplied.

    Returns the matched administrative word, or None if the domain's
    first label isn't a multi-part hyphenated compound containing one.
    """

    hostname = _clean_hostname(domain)
    first_label = hostname.split(".")[0]
    parts = first_label.split("-")

    if len(parts) < 2:
        return None

    for part in parts:
        if part in COMBOSQUAT_ADMIN_WORDS:
            return part

    return None


def compare_domains(claimed_name: str, domain: str) -> dict:
    """
    Compare a claimed organization name with a domain name.

    IMPORTANT distinction — "exact_match" means the domain's ENTIRE first
    label is the brand token and nothing else. If the brand name is only
    PART of a longer hyphenated compound (e.g. "netflix-billing-support",
    "bank-kyc-verification"), that is exactly how combosquatting/lookalike
    domains are constructed — a perfect brand-name substring is not a
    trustworthy signal on its own, so it must NOT be treated as a
    confirmed official match just because the extracted brand token
    matches 100%. Such domains fall through to `possible_typosquatting`
    instead, alongside classic character-level lookalikes.

    Tradeoff: with no maintained per-brand "official domain" list (which
    would need hardcoding every company — explicitly out of scope), this
    heuristic cannot distinguish a deceptive compound domain from one a
    company might legitimately register (e.g. a real "microsoft-teams"
    style product domain). It deliberately favors catching real
    combosquatting attempts over avoiding that rare false positive — and
    this is only one input signal among several in ScamShield's broader
    deterministic + Gemini pipeline, not an automatic verdict on its own.
    """

    claimed = claimed_name.lower().replace(" ", "")
    hostname = _clean_hostname(domain)
    first_label = hostname.split(".")[0]
    core_token = normalize_domain(domain)

    similarity = ratio(claimed, core_token)

    is_single_label_match = first_label == core_token
    exact_match = similarity == 100 and is_single_label_match

    return {
        "claimed_name": claimed_name,
        "domain": domain,
        "normalized_domain": core_token,
        "similarity": round(similarity, 2),
        "possible_typosquatting": similarity >= 70 and not exact_match,
        "exact_match": exact_match,
    }
