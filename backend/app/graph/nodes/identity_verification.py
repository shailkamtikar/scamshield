from app.graph.state import ScamShieldState
from app.graph.signals import make_signal
from app.services.domain_analysis import compare_domains
from app.services.url_normalize import normalize_url


def identity_verification_node(state: ScamShieldState) -> ScamShieldState:
    """
    Compare the claimed organization with each extracted URL.
    """

    if not state.claimed_organization:
        return state

    for url in state.urls:
        normalized = normalize_url(url)
        result = compare_domains(
            state.claimed_organization,
            url,
        )

        if result["exact_match"]:
            state.evidence.append(
                f"{url}: domain matches the claimed organization "
                f"'{state.claimed_organization}'."
            )
            # A confirmed match is reassuring, not a risk signal — it
            # deliberately contributes 0 points and is not added to
            # state.signals.

        elif result["possible_typosquatting"]:
            description = (
                f"{url}: possible impersonation of "
                f"'{state.claimed_organization}' "
                f"(domain similarity: {result['similarity']}%)."
            )
            state.evidence.append(description)
            state.signals.append(
                make_signal(
                    "BRAND_IMPERSONATION",
                    description,
                    "identity_verification",
                    target=normalized,
                )
            )

        else:
            state.evidence.append(
                f"{url}: domain does not closely match "
                f"the claimed organization "
                f"'{state.claimed_organization}' "
                f"(similarity: {result['similarity']}%)."
            )

    return state
