import { MODES } from "./modes";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export class InvestigationError extends Error {
  constructor(message, { status } = {}) {
    super(message);
    this.name = "InvestigationError";
    this.status = status;
  }
}

/** Incrementally parses a Server-Sent-Events byte stream into {event, data}. */
export function createSseParser(onEvent) {
  let buffer = "";
  return (chunk) => {
    buffer += chunk.replace(/\r\n/g, "\n");
    let boundary;
    while ((boundary = buffer.indexOf("\n\n")) !== -1) {
      const block = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      let event = "message";
      const dataLines = [];
      for (const line of block.split("\n")) {
        if (line.startsWith(":")) continue; // heartbeat / comment
        if (line.startsWith("event:")) event = line.slice(6).trim();
        else if (line.startsWith("data:")) dataLines.push(line.slice(5).trimStart());
      }
      if (dataLines.length) {
        try {
          onEvent({ event, data: JSON.parse(dataLines.join("\n")) });
        } catch {
          /* ignore malformed block */
        }
      }
    }
  };
}

function endpointFor(mode, { fromCamera }) {
  if (mode === MODES.TEXT) return "/investigate";
  if (mode === MODES.IMAGE) return "/investigate/image";
  return fromCamera ? "/investigate/qr-text" : "/investigate/qr";
}

function requestFor(mode, input, stream) {
  const fromCamera = Boolean(input.qrText);
  const path = endpointFor(mode, { fromCamera }) + (stream ? "/stream" : "");
  const url = `${API_BASE_URL}${path}`;
  const org = input.claimedOrganization?.trim() || null;

  if (mode === MODES.TEXT) {
    return [url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ message: input.message, source: "web", claimed_organization: org }) }];
  }
  if (fromCamera) {
    return [url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: input.qrText, claimed_organization: org }) }];
  }
  const form = new FormData();
  form.append("file", input.file);
  if (org) form.append("claimed_organization", org);
  return [url, { method: "POST", body: form }];
}

async function readError(response) {
  let detail = `The ScamShield engine returned an error (HTTP ${response.status}).`;
  try {
    const body = await response.json();
    if (typeof body?.detail === "string") detail = body.detail;
    else if (Array.isArray(body?.detail)) detail = "The content could not be processed. Check what you entered and try again.";
  } catch {
    /* keep default */
  }
  return new InvestigationError(detail, { status: response.status });
}

/**
 * Run an investigation, streaming real progress events from the backend.
 * Falls back to the plain endpoint if streaming is unavailable.
 */
export async function investigate(mode, input, { onEvent, signal } = {}) {
  const started = performance.now();
  const [url, init] = requestFor(mode, input, true);
  let final = null;
  let gotEvent = false;

  try {
    const response = await fetch(url, { ...init, signal });
    if (!response.ok) throw await readError(response);
    if (!response.body) throw new Error("no stream");

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    const feed = createSseParser((evt) => {
      gotEvent = true;
      if (evt.event === "done") final = evt.data;
      else if (evt.event === "error") throw new InvestigationError(evt.data.message || "The analysis failed.", { status: evt.data.status });
      onEvent?.(evt);
    });
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      feed(decoder.decode(value, { stream: true }));
    }
  } catch (err) {
    if (err.name === "AbortError") throw err;
    if (err instanceof InvestigationError) throw err;
    if (!gotEvent) {
      // streaming unavailable: use the plain endpoint
      try {
        const [plainUrl, plainInit] = requestFor(mode, input, false);
        const response = await fetch(plainUrl, { ...plainInit, signal });
        if (!response.ok) throw await readError(response);
        final = await response.json();
      } catch (inner) {
        if (inner.name === "AbortError" || inner instanceof InvestigationError) throw inner;
        throw new InvestigationError("Could not reach the ScamShield engine. Make sure the backend is running.");
      }
    } else {
      throw new InvestigationError("The connection to the engine was interrupted. Please try again.");
    }
  }

  if (!final || !final.verdict) throw new InvestigationError("The engine returned an unexpected response.");
  return { result: final, latencyMs: Math.round(performance.now() - started) };
}

export async function fetchHealth() {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, { signal: AbortSignal.timeout(5000) });
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}
