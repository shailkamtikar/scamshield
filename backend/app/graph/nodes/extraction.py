import re

from app.graph.state import ScamShieldState
from app.services.url_normalize import normalize_url


URL_PATTERN = r"https?://[^\s<>\[\]()]+"

TRAILING_PUNCTUATION = ".,!?;:'\""


def extraction_node(state: ScamShieldState) -> ScamShieldState:
    """
    Extract URLs from the user's message and store them in the graph state.
    """

    message = state.message

    urls = re.findall(URL_PATTERN, message)

    cleaned_urls = [
        url.rstrip(TRAILING_PUNCTUATION)
        for url in urls
    ]

    # Drop repeats of the same destination (e.g. the same link pasted
    # twice) so downstream nodes don't investigate it more than once.
    seen_normalized: set[str] = set()
    deduplicated_urls = []
    for url in cleaned_urls:
        key = normalize_url(url)
        if key in seen_normalized:
            continue
        seen_normalized.add(key)
        deduplicated_urls.append(url)

    state.urls = deduplicated_urls

    return state