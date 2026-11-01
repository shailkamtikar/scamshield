"""The result names who is being imitated, by which address, and the real addresses to compare with (the "real vs fake" block)."""

import pytest

from app.engine.analysis import Case, investigate_sync


def run(text):
    return investigate_sync(Case(text, network=False)).result


def one(text):
    r = run(text)
    assert r["impersonations"], r["message_signals"]
    return r["impersonations"][0]


@pytest.mark.parametrize(
    "text,brand,reason,owner",
    [
        ("HSBC Bank: your account is locked. Verify now at https://hbsc-bank.com/login", "HSBC", "BRAND_LOOKALIKE", "hbsc-bank.com"),  # two letters swapped
        ("HSBC alert: confirm your details at http://hsbc.secure-kyc-login.info/verify", "HSBC", "BRAND_IN_SUBDOMAIN_OR_PATH", "secure-kyc-login.info"),
        ("Your SBI account will be blocked. Update KYC at http://sbi-kyc-update.top/login", "SBI", "BRAND_COMBOSQUAT", "sbi-kyc-update.top"),
        ("Amazon refund ready, claim at http://arnazon.in/refund", "Amazon", "BRAND_LOOKALIKE", "arnazon.in"),
        ("Your Paytm KYC is pending, tap http://patym-kyc.in/update", "Paytm", "BRAND_LOOKALIKE", "patym-kyc.in"),
    ],
)
def test_each_imitation_names_its_brand_address_and_owner(text, brand, reason, owner):
    item = one(text)
    assert item["brand"] == brand and item["reason"] == reason and item["owner"] == owner
    assert item["kind"] == "link" and item["official"] and owner not in item["official"]


def test_the_real_addresses_come_from_the_registry_for_that_brand():
    assert "hsbc.co.in" in one("HSBC Bank: verify at https://hbsc-bank.com/login")["official"]
    assert "sbi.co.in" in one("SBI: update KYC at http://sbi-kyc-update.top/login")["official"]


def test_different_messages_give_different_comparisons():
    a = one("HSBC Bank: verify at https://hbsc-bank.com/login")
    b = one("Axis Bank: your KYC expires today. Update at https://axisbank.co.in-verify.xyz/")
    assert a["brand"] != b["brand"] and a["official"] != b["official"] and a["shown"] != b["shown"]


@pytest.mark.parametrize(
    "text",
    [
        "Check this https://www.thehindu.com/news/",
        "Rs 1,200 debited from A/c XX1234. UPI Ref 123456789. -HDFC Bank",
        "Update your KYC in the app: https://netbanking.hdfcbank.com",
        "Your account will be blocked, call 9876543210",  # a threat, but no address imitating anyone
        "Visit https://1.hdfc.bank.in/HDFCBK/s/AAvyG770",
    ],
)
def test_nothing_to_compare_when_no_address_imitates_an_organisation(text):
    assert run(text)["impersonations"] == []


def test_a_brand_inside_a_popular_site_is_still_caught_but_the_real_site_is_not():
    assert run("Pay at https://www.hsbc.co.in/accounts")["impersonations"] == []


def test_email_from_a_lookalike_domain_is_a_sender_comparison():
    raw = "From: Axis Bank <alerts@axisbank-secure-update.com>\nTo: me@example.com\nSubject: Verify your account\nContent-Type: text/plain\n\nPlease verify your account details to avoid suspension.\n"
    r = run(raw)
    item = r["impersonations"][0]
    assert item["kind"] == "sender" and item["brand"] == "Axis Bank" and item["shown"] == "axisbank-secure-update.com"


def test_a_swap_in_a_short_name_is_the_only_new_lookalike_rule_so_ordinary_words_pass():
    for domain in ("https://csdn.net/", "https://example.org/", "https://hubs.com/", "https://access.in/"):
        assert run(domain)["impersonations"] == []
