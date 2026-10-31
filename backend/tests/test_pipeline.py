from app.graph.graph import graph
from app.graph.signals import derive_risk_level
from app.graph.state import ScamShieldState


def run(message, claimed=None):
    return graph.invoke(ScamShieldState(message=message, claimed_organization=claimed))


def categories(result):
    return {signal.category if hasattr(signal, "category") else signal["category"] for signal in result["signals"]}


def test_duplicate_urls_are_deduplicated():
    result = run("go to https://example.com/a and https://example.com/a")
    assert len(result["urls"]) == 1


def test_phishing_message_scores_high():
    result = run(
        "URGENT! Your Microsoft account has been suspended. Click here: https://miconsoft-login.com",
        claimed="Microsoft",
    )
    assert "BRAND_IMPERSONATION" in categories(result)
    assert result["risk_score"] >= 70
    assert result["risk_level"] == "CRITICAL"


def test_legitimate_domain_not_flagged_as_impersonation():
    result = run("Sign in at https://www.microsoft.com/", claimed="Microsoft")
    assert "BRAND_IMPERSONATION" not in categories(result)


def test_no_evidence_is_low():
    result = run("hello, lunch tomorrow?")
    assert result["risk_score"] == 0
    assert result["risk_level"] == "LOW"


def test_social_engineering_categories_detected():
    result = run("Send your OTP immediately or your account will be blocked")
    found = categories(result)
    assert {"CREDENTIAL_REQUEST", "URGENCY", "FEAR_OR_THREAT"} <= found


def test_risk_level_thresholds():
    assert derive_risk_level(0) == "LOW"
    assert derive_risk_level(1) == "MEDIUM"
    assert derive_risk_level(40) == "HIGH"
    assert derive_risk_level(70) == "CRITICAL"


def test_same_url_scores_same_via_text_and_bare():
    a = run("https://secure-login-update.info")
    b = run("please look at https://secure-login-update.info today")
    assert a["risk_score"] == b["risk_score"]
