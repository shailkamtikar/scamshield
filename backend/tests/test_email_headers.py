"""Raw e-mail checks: sender, Reply-To, authentication, attachments, hidden links. Expectations are written by hand."""

from app.engine.analysis import Case, investigate_sync


def run(raw):
    return investigate_sync(Case(raw, network=False)).result


def ids(r):
    return {s["id"] for s in r["message_signals"]}


GENUINE_BANK = """From: HDFC Bank Alerts <alerts@hdfcbank.bank.in>
To: shail@example.com
Subject: Statement for your credit card ending 9981
Date: Fri, 31 Oct 2026 10:00:00 +0530
Authentication-Results: mx.example.com; spf=pass smtp.mailfrom=hdfcbank.bank.in; dkim=pass header.d=hdfcbank.bank.in; dmarc=pass header.from=hdfcbank.bank.in
Content-Type: text/plain; charset=utf-8

Dear Customer, your credit card statement is generated. Total due Rs 14,230, due on 18-Nov-26.
Pay via NetBanking at https://netbanking.hdfcbank.com or the PayZapp app. We never ask for your OTP or PIN.
"""

SPOOF_DISPLAY = """From: SBI Customer Care <support.sbi.care@gmail.com>
To: shail@example.com
Subject: Your account is blocked
Reply-To: sbi.helpdesk.2026@gmail.com
Authentication-Results: mx.example.com; spf=fail; dkim=fail; dmarc=fail
Content-Type: text/plain; charset=utf-8

Your SBI account is blocked. Reply with your account number and OTP to restore it today.
"""

LOOKALIKE_SENDER = """From: Axis Bank <alerts@axisbank-secure-update.com>
To: shail@example.com
Subject: Verify your account
Content-Type: text/plain; charset=utf-8

Please verify your account details to avoid suspension.
"""

EXE_ATTACHMENT = """From: Accounts <accounts@some-vendor.example>
To: shail@example.com
Subject: Invoice 8812
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="b1"

--b1
Content-Type: text/plain; charset=utf-8

Please find the invoice attached.
--b1
Content-Type: application/octet-stream; name="invoice_8812.pdf.exe"
Content-Disposition: attachment; filename="invoice_8812.pdf.exe"
Content-Transfer-Encoding: base64

TVqQAAMAAAAEAAAA
--b1--
"""

HIDDEN_LINK = """From: Paytm Payments <noreply@paytm.com>
To: shail@example.com
Subject: Confirm your wallet
MIME-Version: 1.0
Content-Type: text/html; charset=utf-8

<html><body><p>Confirm your wallet at <a href="http://paytm-wallet-confirm.top/login">https://www.paytm.com/wallet</a> today.</p></body></html>
"""

NEWSLETTER_TRACKED = """From: Flipkart <offers@flipkart.com>
To: shail@example.com
Subject: Big Billion Days: up to 60% off
Authentication-Results: mx.example.com; spf=pass; dkim=pass; dmarc=pass
MIME-Version: 1.0
Content-Type: text/html; charset=utf-8

<html><body><p>Shop now: <a href="https://click.flipkart.com/track?u=abc">www.flipkart.com/bbd</a>. T&amp;C apply. Unsubscribe anytime.</p></body></html>
"""

FORWARDED_FAIL = """From: Priya Sharma <priya.sharma@collegemail.example>
To: shail@example.com
Subject: Notes for tomorrow
Authentication-Results: mx.example.com; spf=fail; dkim=pass; dmarc=none
Content-Type: text/plain; charset=utf-8

Hi, sharing the notes from today's lecture. See you tomorrow.
"""

BEC = """From: Rakesh Mehta - CEO <rakesh.mehta.ceo@gmail.com>
To: accounts@company.example
Subject: Urgent
Reply-To: rakesh.mehta.ceo@gmail.com
Content-Type: text/plain; charset=utf-8

Are you available? I need you to process a wire transfer today. Keep this confidential, I am in a meeting.
"""


def test_genuine_bank_email_with_passing_authentication_is_safe():
    r = run(GENUINE_BANK)
    assert r["verdict"] == "SAFE", (r["verdict"], r["message_signals"])
    assert r["email"]["authentication"]["dmarc"] == "pass"


def test_display_name_claiming_a_bank_from_gmail_is_flagged():
    r = run(SPOOF_DISPLAY)
    assert "SENDER_DISPLAY_NAME_MISMATCH" in ids(r) and r["verdict"] in {"SUSPICIOUS", "DANGEROUS"}
    assert r["category"] in {"PHISHING", "SUSPICIOUS_UNVERIFIED", "FRAUD_SCAM"}


def test_lookalike_sender_domain_is_dangerous():
    r = run(LOOKALIKE_SENDER)
    assert "SENDER_LOOKALIKE" in ids(r) and r["verdict"] == "DANGEROUS"


def test_double_extension_executable_attachment_is_dangerous():
    r = run(EXE_ATTACHMENT)
    assert "RISKY_ATTACHMENT" in ids(r) and r["verdict"] == "DANGEROUS" and r["category"] == "MALICIOUS_CONTENT"


def test_link_text_that_names_another_site_is_flagged_and_its_target_is_checked():
    r = run(HIDDEN_LINK)
    assert "LINK_TEXT_MISMATCH" in ids(r)
    assert r["verdict"] == "DANGEROUS"
    assert any("paytm-wallet-confirm.top" in u["url"] for u in r["urls"])


def test_marketing_tracking_links_are_not_a_hidden_link():
    r = run(NEWSLETTER_TRACKED)
    assert "LINK_TEXT_MISMATCH" not in ids(r) and r["verdict"] == "SAFE"
    assert r["category"] in {"SAFE_PROMOTIONAL", "SPAM"}


def test_authentication_failure_alone_does_not_flag_forwarded_mail():
    r = run(FORWARDED_FAIL)
    assert r["verdict"] == "SAFE"


def test_executive_impersonation_from_free_mail_with_payment_request():
    r = run(BEC)
    assert "BEC_PATTERN" in ids(r) and r["verdict"] in {"SUSPICIOUS", "DANGEROUS"}


def test_plain_text_without_headers_is_untouched():
    r = run("From the desk of the principal: school reopens on Monday.")
    assert "email" not in r
