import itertools

from app.engine.signals import CATALOG, make
from app.engine.verdict import assess_url, confidence_for


def sig(*ids):
    return [make(i, "x", "t", "k") for i in ids]


def test_gibberish_is_dangerous_even_if_unreachable():
    a = assess_url(sig("DOMAIN_GIBBERISH"), "UNKNOWN", "NXDOMAIN")
    assert a.verdict == "DANGEROUS" and a.score >= 60


def test_legit_looking_but_nonexistent_is_could_not_verify():
    a = assess_url([], "UNKNOWN", "NXDOMAIN")
    assert a.verdict == "COULD_NOT_VERIFY" and a.score is None


def test_official_domain_is_safe_even_with_404_page():
    assert assess_url(sig("TRUSTED_OFFICIAL"), "OFFICIAL", "NOT_FOUND").verdict == "SAFE"


def test_feed_hit_beats_popularity():
    assert assess_url(sig("TRUSTED_POPULAR", "FEED_HIT"), "POPULAR", "OK").verdict == "DANGEROUS"


def test_unknown_clean_is_safe_but_low_confidence():
    a = assess_url([], "UNKNOWN", "OK")
    conf, _ = confidence_for(a.verdict, a.signals, {"lexical": "done", "trust": "done", "reachability": "done"}, "UNKNOWN")
    assert a.verdict == "SAFE" and conf <= 0.75


def test_free_hosting_page_is_never_plain_safe():
    assert assess_url([], "UNKNOWN", "OK", platform=True).verdict == "SUSPICIOUS"


def test_score_always_matches_verdict_band():
    bands = {"SAFE": (0, 19), "SUSPICIOUS": (20, 59), "DANGEROUS": (60, 100)}
    risky = [k for k, v in CATALOG.items() if v[0] == "risk"][:14]
    for n in range(0, 4):
        for combo in itertools.combinations(risky, n):
            for tier in ("UNKNOWN", "POPULAR", "OFFICIAL"):
                a = assess_url(sig(*combo), tier, "OK")
                lo, hi = bands[a.verdict]
                assert lo <= a.score <= hi


def test_confidence_bounds_and_determinism():
    s = sig("FEED_HIT")
    a, _ = confidence_for("DANGEROUS", s, {"lexical": "done"}, "UNKNOWN")
    b, _ = confidence_for("DANGEROUS", s, {"lexical": "done"}, "UNKNOWN")
    assert a == b and 0.05 <= a <= 0.99


def test_missing_checks_lower_confidence():
    s = sig("BRAND_LOOKALIKE")
    full, _ = confidence_for("DANGEROUS", s, {"lexical": "done", "google_safe_browsing": "done", "reachability": "done"}, "UNKNOWN")
    part, _ = confidence_for("DANGEROUS", s, {"lexical": "done", "google_safe_browsing": "unavailable", "reachability": "unavailable"}, "UNKNOWN")
    assert part < full
