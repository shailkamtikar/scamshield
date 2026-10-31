import pytest

from app.intel import lexical, trust
from app.intel.urls import parse_url


def ids(url):
    p = parse_url(url)
    return [s.id for s in lexical.analyze(p, trust.classify(p))]


def tier(url):
    return trust.classify(parse_url(url)).tier


@pytest.mark.parametrize("url", [
    "https://www.sbi.co.in/web/personal-banking", "https://onlinesbi.sbi/login", "https://uidai.gov.in",
    "https://open.spotify.com/track/abc", "https://www.flipkart.com/", "https://www.bankofbaroda.in/",
])
def test_real_sites_are_official_and_clean(url):
    assert tier(url) == "OFFICIAL" and ids(url) == []


def test_gibberish_domain():
    assert "DOMAIN_GIBBERISH" in ids("http://xkqzjw7vp.top")


def test_real_short_names_not_gibberish():
    for u in ("https://paytm.com", "https://zee5.com", "https://ola.in"):
        assert "DOMAIN_GIBBERISH" not in ids(u)


def test_combosquat_and_typosquat():
    assert "BRAND_COMBOSQUAT" in ids("https://hdfcbank-secure.in")
    assert "BRAND_LOOKALIKE" in ids("https://miconsoft-login.com")
    assert "BRAND_LOOKALIKE" in ids("https://amaz0n-offers.com")


def test_brand_hidden_in_subdomain():
    assert "BRAND_IN_SUBDOMAIN_OR_PATH" in ids("https://paypal.com.evil-site.xyz/login")


def test_subdomain_trick_is_not_trusted():
    assert tier("https://sbi.co.in.evil.com/") == "UNKNOWN"


def test_fake_gov_domain_is_not_trusted():
    assert tier("https://gov-in-verify.com") == "UNKNOWN"


def test_user_content_platform_is_never_trusted():
    assert tier("https://abc.blogspot.com/login") == "UNKNOWN"
    assert "USER_CONTENT_HOST" in ids("https://abc.github.io/x")


def test_plain_unknown_domain_has_no_signals():
    assert ids("https://mycoolbakery.in") == []


def test_risky_file_link():
    assert "RISKY_FILE_LINK" in ids("https://some-site.in/files/setup.exe")
