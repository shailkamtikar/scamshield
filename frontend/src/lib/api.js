const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export class InvestigationError extends Error {
  constructor(message, { status, cause } = {}) {
    super(message);
    this.name = "InvestigationError";
    this.status = status;
    this.cause = cause;
  }
}

const REQUIRED_FIELDS = [
  "risk_score",
  "risk_level",
  "confidence",
  "reasons",
  "recommendation",
  "evidence",
];

async function parseInvestigationResponse(response, startedAt) {
  const latencyMs = Math.round(performance.now() - startedAt);

  if (!response.ok) {
    let detail = `ScamShield backend responded with an error (HTTP ${response.status}).`;
    try {
      const body = await response.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // non-JSON error body — keep the generic message
    }
    throw new InvestigationError(detail, { status: response.status });
  }

  let data;
  try {
    data = await response.json();
  } catch (err) {
    throw new InvestigationError("ScamShield backend returned a malformed response.", {
      cause: err,
    });
  }

  const missing = REQUIRED_FIELDS.filter((key) => !(key in data));
  if (missing.length > 0) {
    throw new InvestigationError(
      `ScamShield backend response is missing expected fields: ${missing.join(", ")}.`
    );
  }

  return { result: data, latencyMs };
}

function networkErrorFrom(err) {
  return new InvestigationError("Could not reach the ScamShield backend. Is it running?", {
    cause: err,
  });
}

/** SMS/Text mode -> POST /investigate (JSON). */
export async function investigateText({ message, claimedOrganization }) {
  const startedAt = performance.now();
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/investigate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        source: "web",
        claimed_organization: claimedOrganization || null,
        image_path: null,
      }),
    });
  } catch (err) {
    throw networkErrorFrom(err);
  }
  return parseInvestigationResponse(response, startedAt);
}

/** SMS Image mode -> POST /investigate/image (multipart upload, real OCR). */
export async function investigateImage({ file, claimedOrganization }) {
  const startedAt = performance.now();
  const form = new FormData();
  form.append("file", file);
  if (claimedOrganization) form.append("claimed_organization", claimedOrganization);

  let response;
  try {
    response = await fetch(`${API_BASE_URL}/investigate/image`, {
      method: "POST",
      body: form,
    });
  } catch (err) {
    throw networkErrorFrom(err);
  }
  return parseInvestigationResponse(response, startedAt);
}

/** QR Code mode -> POST /investigate/qr (multipart upload, real QR decode). */
export async function investigateQr({ file, claimedOrganization }) {
  const startedAt = performance.now();
  const form = new FormData();
  form.append("file", file);
  if (claimedOrganization) form.append("claimed_organization", claimedOrganization);

  let response;
  try {
    response = await fetch(`${API_BASE_URL}/investigate/qr`, {
      method: "POST",
      body: form,
    });
  } catch (err) {
    throw networkErrorFrom(err);
  }
  return parseInvestigationResponse(response, startedAt);
}

/** Lightweight health check against GET / — used for the connection status indicator. */
export async function checkBackendHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/`, { method: "GET" });
    return res.ok;
  } catch {
    return false;
  }
}

export { API_BASE_URL };
