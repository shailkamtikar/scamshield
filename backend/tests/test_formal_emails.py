import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from eval_emails import load  # noqa: E402

from app.engine import explain as explain_mod  # noqa: E402
from app.engine.analysis import Case, investigate_sync  # noqa: E402
from app.engine.explain import explain  # noqa: E402
from app.intel.trust import brand_tokens  # noqa: E402
from app.intel.urls import extract_urls  # noqa: E402
from app.services import gemini  # noqa: E402
from app.services.gemini_schema import GeminiAnalysis  # noqa: E402

EMAILS = load()


@pytest.mark.parametrize("label,name,text", EMAILS, ids=[e[1] for e in EMAILS])
def test_formal_emails(label, name, text):
    r = investigate_sync(Case(text)).result
    if label == "genuine":
        assert r["verdict"] == "SAFE" and r["risk_score"] <= 10, (name, r["verdict"], r["risk_score"], r["decision_path"])
    else:
        assert r["verdict"] in {"SUSPICIOUS", "DANGEROUS"}, name


def test_missing_space_after_full_stop_is_not_a_link():
    assert extract_urls("take it up with your Broker.You may contact support") == []
    assert [u.host_ascii for u in extract_urls("see broker.you or Broker.You/x")] != []


def test_subdomain_words_are_not_brands():
    assert "mail" not in brand_tokens() and "gmail" in brand_tokens()


def test_regulator_portals_are_trusted():
    for url in ("https://smartodr.in/login", "https://www.nse.co.in/x", "https://scores.sebi.gov.in/"):
        assert investigate_sync(Case(url)).result["assurance"] == "verified"


def test_one_brand_mention_plus_ordinary_words_is_not_enough():
    r = investigate_sync(Case("Groww statement: contact us immediately if anything is wrong. Details at https://unknown-site-example.in/help")).result
    assert r["verdict"] == "SAFE"


def test_mismatch_still_counts_when_the_message_actually_pressures():
    r = investigate_sync(Case("Your HDFC Bank account will be blocked today. Update details at https://mybank-portal-help.in/x")).result
    assert r["verdict"] in {"SUSPICIOUS", "DANGEROUS"}


# ---- the AI second opinion needs a concrete, quotable ask
def _run_second_opinion(monkeypatch, text, analysis):
    monkeypatch.setattr(gemini, "analyze", lambda summary: (analysis, "fake"))
    case = investigate_sync(Case(text))
    explain(case)
    return case.result


def fake(**kw):
    base = dict(is_scam_likely=True, scam_type="phishing", asks_for="none", evidence_quote="", reasons=["x"], recommendation="y")
    return GeminiAnalysis(**{**base, **kw})


def test_second_opinion_without_a_quote_is_ignored(monkeypatch):
    r = _run_second_opinion(monkeypatch, "Dear Customer, please find the invoice attached.", fake())
    assert r["verdict"] == "SAFE"


def test_second_opinion_with_invented_quote_is_ignored(monkeypatch):
    r = _run_second_opinion(monkeypatch, "Dear Customer, please find the invoice attached.", fake(asks_for="money", evidence_quote="send 5000 rupees now"))
    assert r["verdict"] == "SAFE"


def test_second_opinion_can_still_catch_a_new_script(monkeypatch):
    text = "Hello dear, I am a lonely engineer abroad. Please buy gift cards worth 20000 and send me the codes."
    r = _run_second_opinion(monkeypatch, text, fake(asks_for="money", evidence_quote="buy gift cards worth 20000"))
    assert r["verdict"] == "SUSPICIOUS" and "L1_LLM_SECOND_OPINION" in r["decision_path"]


@pytest.mark.xfail(reason="known gap: 'enter your password to open it' is still read as a credential request by the rules", strict=True)
def test_bank_mail_naming_its_own_address_is_not_raised(monkeypatch):
    text = "Dear Customer, your ICICI Bank GST invoice is attached. Please add gstinvoice@icicibank.com to your safe sender list and enter your password to open it."
    r = _run_second_opinion(monkeypatch, text, fake(asks_for="secret_code_or_password", evidence_quote="enter your password to open it"))
    assert r["verdict"] == "SAFE"
