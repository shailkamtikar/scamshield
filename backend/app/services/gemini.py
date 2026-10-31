from google import genai
from google.genai import errors as genai_errors

from app.config import settings
from app.services.gemini_schema import GeminiAssessment


class GeminiUnavailable(RuntimeError):
    """No Gemini API key is configured."""


_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not settings.gemini_api_key:
            raise GeminiUnavailable("GEMINI_API_KEY is not configured.")
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


# HTTP status codes worth retrying against the secondary model: rate limiting
# and transient server-side failures. Anything else (auth, bad request,
# schema validation, ...) is a real bug and should not be hidden by a
# fallback call.
RECOVERABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _build_prompt(evidence: list[str], risk_score: int, score_breakdown: list[dict]) -> str:
    evidence_text = "\n".join(f"- {item}" for item in evidence)
    breakdown_text = (
        "\n".join(f"- {item['signal']}: +{item['points']} points" for item in score_breakdown)
        or "(no scored signals)"
    )

    return f"""
You are the reasoning engine for ScamShield, a scam and phishing
detection system.

A separate deterministic engine has already analyzed this content and
computed an AUTHORITATIVE risk score. Your job is to explain that score
in plain language and provide a calibrated confidence — NOT to invent
your own numeric score or override this one.

Deterministic risk score (authoritative, already final): {risk_score}/100

Score breakdown (why the deterministic engine reached that score):
{breakdown_text}

Full evidence trail:
{evidence_text}

Determine the likelihood that the message represents a scam or
phishing attempt, using the evidence and score breakdown above.

Consider:
1. Brand or organization impersonation
2. Suspicious URLs or domains
3. Social engineering tactics
4. Threats, urgency, or suspicious calls to action
5. Relationships between multiple pieces of evidence

Important rules:
- Do not invent evidence beyond what is listed above.
- Do not claim malicious intent is proven unless the evidence proves it.
- Your risk_level should be consistent with the deterministic score above
  (roughly: 0 -> LOW, 1-39 -> MEDIUM, 40-69 -> HIGH, 70-100 -> CRITICAL) —
  it is used for context only, the system does not use it as final output.
- Confidence must reflect the STRENGTH and QUANTITY of the evidence, not
  a fixed default. A single weak signal should score noticeably lower
  confidence than several corroborating strong signals. Little or no
  evidence should produce low confidence.
- Each reason must describe a SPECIFIC piece of evidence (a URL, domain,
  phrase, or tactic). Never write a reason that just restates the numeric
  score or breakdown totals (e.g. do NOT write "the risk score is X/100"
  as a reason) — the score is shown separately, your job is to explain
  the evidence behind it.
- Give a practical safety recommendation.
"""


def _call_model(model: str, prompt: str) -> GeminiAssessment:
    response = _get_client().models.generate_content(
        model=model,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": GeminiAssessment,
        },
    )

    return GeminiAssessment.model_validate_json(response.text)


def analyze_scam_evidence(
    evidence: list[str],
    risk_score: int,
    score_breakdown: list[dict],
) -> tuple[GeminiAssessment, str]:
    """
    Analyze collected ScamShield evidence using Gemini and return a
    validated structured assessment.

    `risk_score`/`score_breakdown` come from the deterministic risk engine
    (already computed before this is called) and are given to Gemini as
    grounding context — Gemini explains and calibrates confidence around
    them, it does not compute or override risk_score itself.

    Tries settings.primary_gemini_model first. Only falls back to
    settings.secondary_gemini_model on a recoverable API failure (rate limiting or
    a transient server error) — never to mask a real bug.

    Returns (assessment, model_name_used).
    """

    prompt = _build_prompt(evidence, risk_score, score_breakdown)

    try:
        assessment = _call_model(settings.primary_gemini_model, prompt)
        return assessment, settings.primary_gemini_model
    except genai_errors.APIError as err:
        if getattr(err, "code", None) not in RECOVERABLE_STATUS_CODES:
            raise

    assessment = _call_model(settings.secondary_gemini_model, prompt)
    return assessment, settings.secondary_gemini_model
