"""
Genuine notices from many sectors must not be flagged; the same wording WITH an unverifiable way to act on it must.

The CSV was written separately from the rules (see scripts/eval_genuine.py). The pasted real-world examples
that exposed the original false alarms are kept in the CSV and in data/benchmark/emails as regression cases.
"""

import csv
from pathlib import Path

import pytest

from app.engine.analysis import Case, investigate_sync

FILE = Path(__file__).resolve().parents[2] / "data" / "benchmark" / "messages_genuine.csv"
ROWS = list(csv.DictReader(open(FILE, encoding="utf-8")))


def run(text):
    return investigate_sync(Case(text, network=False)).result


@pytest.mark.parametrize("row", [r for r in ROWS if r["label"] == "genuine"], ids=lambda r: r["category"] + ":" + r["text"][:30])
def test_genuine_notice_is_not_flagged(row):
    r = run(row["text"])
    assert r["verdict"] == "SAFE" and r["risk_score"] <= 8, (r["verdict"], r["risk_score"], r["message_signals"])


def test_promotions_are_never_flagged_and_mostly_recognised():
    promos = [r for r in ROWS if r["label"] == "promo"]
    results = [run(r["text"]) for r in promos]
    assert all(r["verdict"] == "SAFE" for r in results)
    recognised = sum(1 for r in results if r["category"] in {"SAFE_PROMOTIONAL", "SPAM"})
    assert recognised / len(promos) >= 0.85
    assert sum(1 for r in results if r["category"] == "SAFE_PROMOTIONAL") / len(promos) >= 0.5  # promotions from a named organisation are not called spam


def test_promotion_with_unknown_link_says_destination_is_unverified():
    r = run("Mega sale! Flat 50% off on all shoes. Shop now at https://bit.ly/3xYz9aB. T&C apply.")
    assert r["verdict"] == "SAFE" and r["assurance"] == "spam" and r["category"] == "SPAM" and r["action"] == "SPAM"


def test_promotion_on_official_site_is_marked_promotion():
    r = run("Diwali offer: 20% off on all plans. Upgrade now at https://www.airtel.in/offers. T&C apply.")
    assert r["assurance"] == "promotion"


# ---- the same pressure wording with something to click or call is still a scam
@pytest.mark.parametrize(
    "text",
    [
        "Full KYC Due in 90 days. Update it now here: https://hdfc-kyc-update.online/login",
        "Your account will be blocked today due to pending KYC. Call 9876543210 now to update.",
        "Dear user your electricity will be disconnected tonight. Pay pending bill on https://bescom-pay-now.top/x",
        "Refund of Rs 4,999 is pending, claim it on WhatsApp +91 98765 43210 before it expires.",
        "Your SBI YONO account will be blocked today. Update your PAN immediately: http://sbi-yono-update.in.net/login",
    ],
)
def test_pressure_with_unverified_channel_is_still_flagged(text):
    assert run(text)["verdict"] in {"SUSPICIOUS", "DANGEROUS"}


def test_bank_in_zone_is_official_for_any_bank_subdomain():
    r = run("Dear customer your NCMC card KYC is due. Update at https://1.hdfc.bank.in/HDFCBK/s/AAvyG770")
    assert r["verdict"] == "SAFE" and r["urls"][0]["trust"]["tier"] == "OFFICIAL"


def test_popular_site_does_not_vouch_for_another_brand_in_its_subdomain():
    r = run("http://sbi-yono-update.in.net/login")
    assert "BRAND_IN_SUBDOMAIN_OR_PATH" in {s["id"] for s in r["urls"][0]["signals"]}


def test_updating_pan_is_kyc_wording_not_a_credential_request():
    r = run("Please update your PAN in your bank account before 31-Dec-26. Visit your home branch or use Net Banking.")
    assert "CREDENTIAL_REQUEST" not in {s["id"] for s in r["message_signals"]}


def test_sharing_a_secret_is_still_a_credential_request():
    r = run("Please share your OTP and ATM PIN with our executive to continue.")
    assert r["verdict"] in {"SUSPICIOUS", "DANGEROUS"}


def test_attachment_and_wifi_passwords_are_not_account_secrets():
    for text in (
        "Your statement is attached. Enter your password to open it. The password is your date of birth in DDMMYYYY.",
        "Bro send me the Wi-Fi password please",
    ):
        assert "CREDENTIAL_REQUEST" not in {s["id"] for s in run(text)["message_signals"]}


def test_download_app_from_play_store_is_not_an_apk_install():
    r = run("Download the app from the Play Store to track your order.")
    assert "APK_INSTALL" not in {s["id"] for s in r["message_signals"]}
    assert "APK_INSTALL" in {s["id"] for s in run("Download the app from this link to claim your refund: http://x.top/a.apk")["message_signals"]}


def test_long_pathological_input_is_analysed_quickly():
    """A 40,000-character run of one symbol used to take 7 s (quadratic regular expressions): a cheap way to tie up the server."""
    import time

    for text in ("-" * 40000, "1" * 40000, "a@" * 20000, ".-" * 20000):
        started = time.time()
        run(text)
        assert time.time() - started < 3
