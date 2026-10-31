"""
Category and action on top of the verdict.

The verdict (SAFE / SUSPICIOUS / DANGEROUS / COULD_NOT_VERIFY) answers "how worried should you be". The category answers
"what kind of message is it", so that an advert, a genuine bank notice, spam and a phishing page are never described with the
same word. Everything here is derived from signals the engine already produced; nothing is looked up or invented.

Categories
    SAFE_TRANSACTIONAL   genuine notices, alerts, OTPs, receipts, reminders
    SAFE_PROMOTIONAL     advertising from an identifiable organisation whose link checks out
    SAFE_OTHER           nothing wrong found and nothing to classify (ordinary text, personal messages)
    SPAM                 unwanted advertising: sender or link cannot be tied to an organisation. Not malicious by itself.
    PHISHING             tries to collect credentials, codes or logins, or imitates a brand
    FRAUD_SCAM           money scams: prizes, investments, jobs, fake refunds, collect requests, threats
    MALICIOUS_CONTENT    malware, app/file installs, remote-access tools, confirmed malicious infrastructure
    SUSPICIOUS_UNVERIFIED  not enough evidence either way

Actions
    ALLOW, PROMOTIONAL, SPAM, WARN, BLOCK, VERIFY
"""

MALICIOUS_IDS = {"APK_INSTALL", "APK_DOWNLOAD", "RISKY_FILE_LINK", "DANGEROUS_SCHEME", "REMOTE_ACCESS_APP", "SANDBOX_MALICIOUS", "HOST_FLAGGED_PAGE", "RISKY_ATTACHMENT"}
PHISHING_IDS = {
    "CREDENTIAL_REQUEST", "KYC_UPDATE", "BRAND_LOOKALIKE", "BRAND_COMBOSQUAT", "BRAND_IN_SUBDOMAIN_OR_PATH", "BRAND_IN_DOMAIN",
    "BRAND_MISMATCH_LINK", "BRAND_MISMATCH_PAGE", "ADMIN_COMPOUND", "HOMOGRAPH", "LOGIN_FORM_UNTRUSTED", "FORM_CROSS_DOMAIN",
    "SENDER_DISPLAY_NAME_MISMATCH", "SENDER_LOOKALIKE", "LINK_TEXT_MISMATCH", "AUTH_FAILED", "SUSPICIOUS_ATTACHMENT",
}
SCRIPT_FRAUD_IDS = {"UPI_COLLECT_SCAM", "PRIZE_LOTTERY", "INVESTMENT_SCAM", "JOB_TASK_SCAM", "ARREST_THREAT", "ADVANCE_FEE", "CRYPTO_PAYMENT"}
BRAND_IDS = {"BRAND_LOOKALIKE", "BRAND_COMBOSQUAT", "BRAND_IN_SUBDOMAIN_OR_PATH", "BRAND_IN_DOMAIN", "BRAND_MISMATCH_PAGE", "HOMOGRAPH", "ADMIN_COMPOUND",
             "LOGIN_FORM_UNTRUSTED", "FORM_CROSS_DOMAIN", "SENDER_DISPLAY_NAME_MISMATCH", "SENDER_LOOKALIKE"}
FRAUD_IDS = {
    "PRIZE_LOTTERY", "INVESTMENT_SCAM", "JOB_TASK_SCAM", "UPI_COLLECT_SCAM", "ARREST_THREAT", "FINANCIAL_PRESSURE", "CRYPTO_PAYMENT",
    "UPI_BRAND_PAYEE_MISMATCH", "UPI_UNKNOWN_HANDLE", "PHONE_CALL_TO_ACTION", "LLM_SCAM_INTENT", "REPLY_TO_MISMATCH", "BEC_PATTERN",
}

LABELS = {
    "SAFE_TRANSACTIONAL": "Genuine notice",
    "SAFE_PROMOTIONAL": "Promotion",
    "SAFE_OTHER": "No problems found",
    "SPAM": "Spam",
    "PHISHING": "Phishing",
    "FRAUD_SCAM": "Fraud / scam",
    "MALICIOUS_CONTENT": "Malicious content",
    "SUSPICIOUS_UNVERIFIED": "Suspicious / unverified",
}


def classify(result: dict, mentioned_brand: bool = False) -> dict:
    verdict = result["verdict"]
    assurance = result.get("assurance")
    ids = set(result.get("risk_ids", []))
    mtype = result.get("message_type")

    if verdict == "DANGEROUS":
        if ids & MALICIOUS_IDS:
            category = "MALICIOUS_CONTENT"
        elif ids & SCRIPT_FRAUD_IDS and not ids & BRAND_IDS:
            category = "FRAUD_SCAM"
        elif ids & PHISHING_IDS:
            category = "PHISHING"
        elif ids & FRAUD_IDS:
            category = "FRAUD_SCAM"
        elif ids & {"FEED_HIT", "VT_MALICIOUS_MANY"}:
            category = "PHISHING"  # feeds list phishing and malware; without malware evidence the usual case is phishing
        else:
            category = "PHISHING" if any(u["verdict"] == "DANGEROUS" for u in result.get("urls", [])) else "FRAUD_SCAM"
        action = "BLOCK"
    elif verdict == "SUSPICIOUS":
        category, action = "SUSPICIOUS_UNVERIFIED", "WARN"
    elif verdict == "COULD_NOT_VERIFY":
        category, action = "SUSPICIOUS_UNVERIFIED", "VERIFY"
    else:  # SAFE
        if assurance == "promotion":
            category, action = ("SAFE_PROMOTIONAL", "PROMOTIONAL") if mentioned_brand else ("SPAM", "SPAM")
        elif assurance == "promotion_unverified":
            category, action = "SPAM", "SPAM"
        elif mtype in {"otp", "transaction"}:
            category, action = "SAFE_TRANSACTIONAL", "ALLOW"
        elif assurance == "verified":
            category, action = "SAFE_OTHER", "ALLOW"
        elif assurance == "valid_payment":
            category, action = "SAFE_TRANSACTIONAL", "VERIFY"
        elif assurance == "no_problems_found":
            category, action = "SAFE_OTHER", "VERIFY"  # nothing found is not proof of safety
        else:
            category, action = "SAFE_OTHER", "ALLOW"
    return {"category": category, "category_label": LABELS[category], "action": action}


def apply(result: dict, mentioned_brand: bool = False) -> None:
    result.update(classify(result, mentioned_brand))
    if result["category"] == "SPAM":
        result["assurance"] = "spam"  # the screen shows spam in grey, apart from genuine promotions (blue)
