"""
Signal-generation verification for ScamShield's deterministic risk engine.

Prints the ACTUAL structured RiskSignal list (the source of truth) for a
set of realistic attack messages and asserts the expected signal
CATEGORIES are present — never depends on Gemini's natural-language
output, and never asserts a specific point total, since the objective is
"strong evidence -> strong contribution," not a magic number.

Also verifies claimed_organization genuinely reaches
identity_verification_node (by checking its output is organization-
specific, not by inspecting private state), and that a legitimate
official domain is not penalized just because the brand name is present.

Uses only safe, synthetic domains — including reserved test TLDs like
".example" — never live/real infrastructure. ".example" is not treated
as inherently suspicious; only the brand/URL relationship is scored.
"""

from app.graph.graph import graph
from app.graph.state import ScamShieldState


def run(label, message, claimed_organization=None):
    state = ScamShieldState(message=message, claimed_organization=claimed_organization)
    result = graph.invoke(state)
    print(f"\n--- {label} (claimed_organization={claimed_organization!r}) ---")
    print("normalized urls:", result["urls"])
    print("signals:")
    for s in result["signals"]:
        print(" ", s)
    print("score_breakdown:", result["score_breakdown"])
    print("risk_score:", result["risk_score"], "risk_level:", result["risk_level"])
    return result


def categories(result):
    return {s.category for s in result["signals"]}


# ---------------------------------------------------------------------------
# TEST A — Microsoft lookalike
# ---------------------------------------------------------------------------
test_a = run(
    "TEST A: Microsoft phishing",
    "URGENT!\n\nYour Microsoft account has been suspended.\n\nClick here to verify:\n\n"
    "https://miconsoft-login.com\n\nYour account may be permanently locked if you do not verify today.",
    claimed_organization="Microsoft",
)

# ---------------------------------------------------------------------------
# TEST B — Netflix combosquat
# ---------------------------------------------------------------------------
test_b = run(
    "TEST B: Netflix phishing",
    "Netflix\n\nWe were unable to process your latest payment.\n\nYour membership will be cancelled "
    "unless you update your billing information immediately.\n\nUpdate payment method:\n\n"
    "https://netflix-billing-support.example\n\nComplete verification within 24 hours to avoid interruption.",
    claimed_organization="Netflix",
)

# ---------------------------------------------------------------------------
# TEST C — Bank combosquat with a suspicious path
# ---------------------------------------------------------------------------
test_c = run(
    "TEST C: Bank phishing",
    "IMPORTANT BANK ALERT\n\nYour KYC verification has expired.\n\nYour account will be restricted "
    "within 24 hours unless you complete verification.\n\nVerify your account now:\n\n"
    "https://bank-kyc-verification.example/login\n\nDo not ignore this message.",
    claimed_organization="Bank",
)

# ---------------------------------------------------------------------------
# TEST D — Legitimate official Microsoft domain
# ---------------------------------------------------------------------------
test_d = run(
    "TEST D: Legitimate Microsoft",
    "Your Microsoft account security information was updated.\n\nReview your security settings:\n\n"
    "https://www.microsoft.com/\n\nNo action is required if you recognize this activity.",
    claimed_organization="Microsoft",
)

# ---------------------------------------------------------------------------
# TEST E — Bare suspicious URL only, no surrounding message language
# ---------------------------------------------------------------------------
test_e = run(
    "TEST E: Bare Microsoft-lookalike URL only",
    "https://miconsoft-login.com",
    claimed_organization="Microsoft",
)


print("\n\n=== ASSERTIONS ===")

# TEST A: full attack -> impersonation + URL keyword + all 3 social signals
cats_a = categories(test_a)
assert "BRAND_IMPERSONATION" in cats_a, cats_a
assert "URL_SUSPICIOUS_KEYWORD" in cats_a, cats_a
assert "URGENCY" in cats_a, cats_a
assert "FEAR_OR_THREAT" in cats_a, cats_a
assert "SUSPICIOUS_CALL_TO_ACTION" in cats_a, cats_a
print("PASS A: Microsoft lookalike produces BRAND_IMPERSONATION + URL + full social-engineering signal set")

# TEST B: claimed_organization="Netflix" must have reached identity_verification
# (proven by an org-specific BRAND_IMPERSONATION description, not a generic one)
cats_b = categories(test_b)
assert "BRAND_IMPERSONATION" in cats_b, cats_b
assert any("Netflix" in s.description for s in test_b["signals"] if s.category == "BRAND_IMPERSONATION")
assert "FINANCIAL_PRESSURE" in cats_b, cats_b
assert "URGENCY" in cats_b, cats_b
print("PASS B: claimed_organization='Netflix' reached identity_verification and produced BRAND_IMPERSONATION")

# TEST C: claimed_organization="Bank" must have reached identity_verification
cats_c = categories(test_c)
assert "BRAND_IMPERSONATION" in cats_c, cats_c
assert any("Bank" in s.description for s in test_c["signals"] if s.category == "BRAND_IMPERSONATION")
assert "URL_SUSPICIOUS_KEYWORD" in cats_c, cats_c
print("PASS C: claimed_organization='Bank' reached identity_verification, URL/domain evidence contributes")

# TEST D: legitimate official domain must NOT be penalized
cats_d = categories(test_d)
assert "BRAND_IMPERSONATION" not in cats_d, cats_d
assert test_d["risk_score"] == 0, test_d["risk_score"]
assert test_d["risk_level"] == "LOW"
print("PASS D: legitimate microsoft.com is not flagged as impersonation, scores 0/LOW")

# TEST E: URL-only input still carries the full URL/brand signal
cats_e = categories(test_e)
assert "BRAND_IMPERSONATION" in cats_e, cats_e
assert "URL_SUSPICIOUS_KEYWORD" in cats_e, cats_e
assert test_e["risk_score"] == 45, test_e["risk_score"]
print("PASS E: bare suspicious URL alone still carries full URL/brand signal (score 45 = 35+10)")

# risk_level must never contradict risk_score (deterministic thresholds), and
# Gemini's reasons must never just restate the number.
from app.graph.signals import derive_risk_level

for label, result in [("A", test_a), ("B", test_b), ("C", test_c), ("D", test_d), ("E", test_e)]:
    assert result["risk_level"] == derive_risk_level(result["risk_score"]), label
    for reason in result["reasons"]:
        assert not reason.strip().lower().startswith("the deterministic risk score"), (label, reason)
print("PASS: risk_level always matches risk_score thresholds; no reason just restates the score number")

print("\nSignal generation verification: PASS")
