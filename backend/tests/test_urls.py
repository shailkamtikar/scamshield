from app.intel.urls import extract_urls, parse_url


def hosts(text):
    return [u.host_ascii for u in extract_urls(text)]


def test_scheme_less_urls_found():
    assert hosts("visit sbi-kyc-update.com/login now") == ["sbi-kyc-update.com"]


def test_defanged_urls_are_refanged():
    assert hosts("hxxps://evil[.]com/a") == ["evil.com"]


def test_prose_is_not_a_url():
    assert hosts("e.g. file.txt and v1.2.3 and i.e. nothing") == []


def test_email_domain_is_not_a_link():
    assert hosts("write to someone@example.com please") == []


def test_duplicates_removed():
    assert len(extract_urls("https://a.com/x and https://www.a.com/x")) == 1


def test_homograph_flagged():
    p = parse_url("https://аpple.com")
    assert p and "MIXED_SCRIPT" in p.flags


def test_userinfo_trick_goes_to_real_host():
    p = parse_url("https://sbi.co.in@evil.com/x")
    assert p.host_ascii == "evil.com" and "USERINFO_TRICK" in p.flags


def test_invisible_chars_flagged():
    p = parse_url("https://pay​tm.com")
    assert p and "INVISIBLE_CHARS" in p.flags


def test_raw_ip():
    assert parse_url("http://192.168.4.4/login").is_ip


def test_huge_text_is_fast():
    import time

    start = time.time()
    extract_urls("a" * 200000 + " http://x.com")
    assert time.time() - start < 3
