from app.graph.state import ScamShieldState
from app.graph.signals import make_signal


SOCIAL_ENGINEERING_PATTERNS = {
    "urgency": [
        "urgent",
        "immediately",
        "act now",
        "right away",
        "as soon as possible",
        "within 24 hours",
    ],
    "fear_or_threat": [
        "suspended",
        "blocked",
        "closed",
        "terminated",
        "locked",
        "legal action",
        "police",
        "penalty",
    ],
    "credential_request": [
        "password",
        "otp",
        "one time password",
        "verification code",
        "pin",
        "cvv",
    ],
    "financial_pressure": [
        "payment",
        "pay now",
        "transfer",
        "refund",
        "prize",
        "money",
        "bank account",
    ],
    "suspicious_call_to_action": [
        "click here",
        "click the link",
        "open the link",
        "verify now",
        "confirm now",
        "download",
        "call immediately",
    ],
}

# Maps each detection category above to its scoring signal category
# (app.graph.signals.CATEGORY_POINTS). Every category that can be
# detected here must appear so evidence is never silently unscored.
CATEGORY_TO_SIGNAL = {
    "urgency": "URGENCY",
    "fear_or_threat": "FEAR_OR_THREAT",
    "credential_request": "CREDENTIAL_REQUEST",
    "financial_pressure": "FINANCIAL_PRESSURE",
    "suspicious_call_to_action": "SUSPICIOUS_CALL_TO_ACTION",
}


def social_engineering_node(state: ScamShieldState) -> ScamShieldState:
    """
    Detect common social engineering indicators in the message.
    """

    message = state.message.lower()

    for category, patterns in SOCIAL_ENGINEERING_PATTERNS.items():
        for pattern in patterns:
            if pattern in message:
                description = (
                    f"Social engineering indicator: "
                    f"{category.replace('_', ' ')} "
                    f"('{pattern}')."
                )
                state.evidence.append(description)
                # target=None: this is a message-level signal, not tied to
                # a specific URL. Multiple keyword hits within the same
                # category are deduplicated at scoring time (same
                # category, same target=None), matching one real-world
                # tactic rather than being counted once per keyword.
                state.signals.append(
                    make_signal(
                        CATEGORY_TO_SIGNAL[category],
                        description,
                        "social_engineering",
                        target=None,
                    )
                )

    return state
