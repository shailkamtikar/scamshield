"""
Signal vocabulary: every piece of evidence the engine can produce, with its
polarity, strength and point weight. This table is the ONLY place weights
live. Gemini never sets or changes any of them.
"""

from dataclasses import dataclass, field

WEIGHTS_VERSION = "2.0"

# id -> (polarity, points, strength, short label)
CATALOG: dict[str, tuple[str, int, str, str]] = {
    # --- threat intelligence (decisive) ---
    "FEED_HIT": ("risk", 100, "decisive", "Listed as malicious by a threat feed"),
    "VT_MALICIOUS_MANY": ("risk", 80, "decisive", "Flagged malicious by many antivirus engines"),
    "ML_DOMAIN_RISK": ("risk", 22, "moderate", "Learned model: this domain name resembles known phishing domains"),
    "VT_MALICIOUS_FEW": ("risk", 12, "weak", "Flagged by one or two security engines"),
    # --- brand / lookalike ---
    "BRAND_LOOKALIKE": ("risk", 60, "strong", "Misspelled lookalike of a known brand"),
    "BRAND_COMBOSQUAT": ("risk", 55, "strong", "Brand name combined with account/security words"),
    "BRAND_IN_SUBDOMAIN_OR_PATH": ("risk", 45, "strong", "Brand name used on a domain that is not theirs"),
    "BRAND_MISMATCH_LINK": ("risk", 30, "moderate", "Message names one organization but links to another domain"),
    "BRAND_IN_DOMAIN": ("risk", 25, "moderate", "Brand name inside an unrelated domain"),
    "ADMIN_COMPOUND": ("risk", 25, "moderate", "Domain built from account/security words"),
    # --- domain structure ---
    "DOMAIN_GIBBERISH": ("risk", 45, "strong", "Random-looking domain name"),
    "HOMOGRAPH": ("risk", 60, "strong", "Look-alike Unicode characters in domain"),
    "INVISIBLE_CHARS": ("risk", 50, "strong", "Hidden/invisible characters in the link"),
    "USERINFO_TRICK": ("risk", 50, "strong", "Deceptive 'user@host' trick in the link"),
    "PUNYCODE": ("risk", 15, "weak", "Internationalised (punycode) domain"),
    "RAW_IP": ("risk", 45, "strong", "Link uses a raw IP address"),
    "OBFUSCATED_IP": ("risk", 55, "strong", "Link hides an IP address in an encoded form"),
    "RISKY_TLD": ("risk", 10, "weak", "Domain ending commonly abused by scammers"),
    "DEEP_SUBDOMAINS": ("risk", 12, "weak", "Unusually many subdomains"),
    "MANY_HYPHENS": ("risk", 10, "weak", "Domain with many hyphens"),
    "LONG_HOSTNAME": ("risk", 8, "weak", "Very long hostname"),
    "SHORTENER": ("risk", 8, "weak", "Shortened link hides the real destination"),
    "NO_HTTPS": ("risk", 8, "weak", "Link does not use HTTPS"),
    "USER_CONTENT_HOST": ("risk", 14, "weak", "Hosted on a free page-hosting platform"),
    "REDIRECT_TO_OTHER_DOMAIN": ("risk", 4, "weak", "Redirects to a different domain"),
    "REDIRECT_CHAIN_LONG": ("risk", 10, "weak", "Long chain of redirects"),
    # --- domain facts ---
    "DOMAIN_AGE_LT_30D": ("risk", 35, "strong", "Domain registered less than 30 days ago"),
    "DOMAIN_AGE_LT_1Y": ("risk", 8, "weak", "Domain registered less than a year ago"),
    "CERT_NEW": ("risk", 6, "weak", "Brand-new TLS certificate"),
    "CERT_MISMATCH": ("risk", 15, "weak", "The site's security certificate is not valid"),
    "NO_TLS": ("risk", 8, "weak", "Site has no working HTTPS"),
    # --- page inspection ---
    "HOST_FLAGGED_PAGE": ("risk", 90, "decisive", "The hosting provider has flagged this page"),
    "SANDBOX_MALICIOUS": ("risk", 90, "decisive", "A real browser sandbox judged this page malicious"),
    "BRAND_MENTION_PAGE": ("risk", 8, "weak", "Page title mentions a brand it may not belong to"),
    "LOGIN_FORM_UNTRUSTED": ("risk", 12, "weak", "Asks for a password on an unverified site"),
    "FORM_CROSS_DOMAIN": ("risk", 35, "strong", "Form sends data to a different domain"),
    "BRAND_MISMATCH_PAGE": ("risk", 45, "strong", "Page pretends to be a brand it does not belong to"),
    "APK_DOWNLOAD": ("risk", 30, "moderate", "Page pushes an app (APK) download"),
    "RISKY_FILE_LINK": ("risk", 35, "moderate", "Link downloads an executable or app file"),
    "PAGE_PARKED_OR_EMPTY": ("risk", 4, "weak", "Page is empty or parked"),
    # --- message language ---
    "URGENCY": ("risk", 10, "weak", "Urgency language"),
    "FEAR_OR_THREAT": ("risk", 15, "moderate", "Fear / threat language"),
    "CREDENTIAL_REQUEST": ("risk", 25, "strong", "Asks for OTP / PIN / password / card details"),
    "FINANCIAL_PRESSURE": ("risk", 15, "moderate", "Financial pressure or reward bait"),
    "SUSPICIOUS_CTA": ("risk", 8, "weak", "Pushes you to click or call"),
    "KYC_UPDATE": ("risk", 20, "moderate", "Fake KYC / account-update pretext"),
    "ADVANCE_FEE": ("risk", 35, "strong", "Asks you to pay a fee before you get money, a job or a prize"),
    # --- e-mail structure (only when the headers / HTML were pasted) ---
    "SENDER_LOOKALIKE": ("risk", 60, "strong", "Sender's address imitates a known organisation"),
    "SENDER_DISPLAY_NAME_MISMATCH": ("risk", 45, "strong", "Sender's name claims an organisation its address does not belong to"),
    "REPLY_TO_MISMATCH": ("risk", 15, "weak", "Replies go to a different domain than the sender"),
    "AUTH_FAILED": ("risk", 15, "weak", "The sender could not be authenticated"),
    "RISKY_ATTACHMENT": ("risk", 70, "strong", "Attachment is a program or script"),
    "SUSPICIOUS_ATTACHMENT": ("risk", 25, "moderate", "Attachment type often used to carry macros or fake pages"),
    "LINK_TEXT_MISMATCH": ("risk", 40, "strong", "A link shows one address but goes to another"),
    "BEC_PATTERN": ("risk", 40, "strong", "Payment or secrecy request from an address that does not match who it claims to be"),
    "PRIZE_LOTTERY": ("risk", 20, "moderate", "Prize / lottery bait"),
    "JOB_TASK_SCAM": ("risk", 25, "moderate", "Work-from-home / task-payment scam pattern"),
    "REMOTE_ACCESS_APP": ("risk", 30, "strong", "Asks you to install a remote-access app"),
    "APK_INSTALL": ("risk", 30, "moderate", "Asks you to install an app file"),
    "ARREST_THREAT": ("risk", 25, "strong", "Fake police / arrest / 'digital arrest' threat"),
    "INVESTMENT_SCAM": ("risk", 20, "moderate", "Investment / crypto guaranteed-returns bait"),
    "UPI_COLLECT_SCAM": ("risk", 30, "strong", "Asks you to scan or approve to RECEIVE money"),
    "PHONE_CALL_TO_ACTION": ("risk", 10, "weak", "Asks you to call an unknown number"),
    "SENDER_PERSONAL_NUMBER": ("risk", 10, "weak", "Claims to be an organization but came from a personal number"),
    "LLM_SCAM_INTENT": ("risk", 20, "moderate", "AI reading of the message indicates scam intent"),
    "PROMPT_INJECTION": ("risk", 15, "moderate", "Text tries to instruct the analysis system"),
    "OCR_VISION_MISMATCH": ("risk", 5, "weak", "Two readers disagreed about the text"),
    # --- QR / UPI ---
    "UPI_UNKNOWN_HANDLE": ("risk", 25, "moderate", "UPI address uses an unknown bank handle"),
    "UPI_BRAND_PAYEE_MISMATCH": ("risk", 45, "strong", "Payee name claims a brand its address does not match"),
    "UPI_MALFORMED": ("risk", 20, "moderate", "Malformed UPI payment request"),
    "DANGEROUS_SCHEME": ("risk", 90, "decisive", "QR runs code or an unsafe link type"),
    "CRYPTO_PAYMENT": ("risk", 20, "moderate", "Cryptocurrency payment request (irreversible)"),
    "PREMIUM_SMS": ("risk", 25, "moderate", "QR pre-fills an SMS to a short code"),
    "OPEN_WIFI": ("risk", 10, "weak", "Open (unencrypted) Wi-Fi network"),
    # --- trust ---
    "TRUSTED_OFFICIAL": ("trust", 40, "strong", "Verified official domain"),
    "TRUSTED_POPULAR": ("trust", 25, "moderate", "Widely used, well-known site"),
    "DOMAIN_AGE_GT_5Y": ("trust", 12, "moderate", "Domain has existed for more than 5 years"),
    "SANDBOX_CLEAN": ("trust", 15, "moderate", "A real browser sandbox found nothing malicious"),
    "REPUTATION_CLEAN": ("trust", 10, "moderate", "No threat feed lists this link"),
    "GENUINE_ALERT_PATTERN": ("trust", 15, "moderate", "Matches a genuine bank-alert template"),
    "VERIFIED_SERVICE": ("trust", 40, "strong", "QR points to a verified service"),
    "UPI_VALID": ("trust", 30, "moderate", "Well-formed UPI payment request"),
}


@dataclass
class Signal:
    id: str
    explanation: str
    source: str
    target: str | None = None  # normalised URL/domain key; None = message-level
    brand: str | None = None  # organisation this evidence says is being imitated (shown as "real vs fake")
    shown: str | None = None  # the address (link host or sender domain) that imitates it
    polarity: str = field(init=False)
    points: int = field(init=False)
    strength: str = field(init=False)
    label: str = field(init=False)

    def __post_init__(self):
        polarity, points, strength, label = CATALOG[self.id]
        self.polarity, self.points, self.strength, self.label = polarity, points, strength, label

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "polarity": self.polarity,
            "points": self.points,
            "strength": self.strength,
            "explanation": self.explanation,
            "source": self.source,
            "target": self.target,
        }


def make(signal_id: str, explanation: str, source: str, target: str | None = None, brand: str | None = None, shown: str | None = None) -> Signal:
    return Signal(signal_id, explanation, source, target, brand, shown)


def dedupe(signals: list[Signal]) -> list[Signal]:
    seen: dict[tuple[str, str | None], Signal] = {}
    for s in signals:
        seen.setdefault((s.id, s.target), s)
    return list(seen.values())
