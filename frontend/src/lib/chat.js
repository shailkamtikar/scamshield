import { API_BASE_URL, createSseParser } from "./api";
import { defang } from "./format";
import { getVerdict } from "./verdict";

/** Short, plain summary of the current result so the assistant can explain it. */
export function summariseResult(result) {
  if (!result) return null;
  const v = getVerdict(result.verdict, result.assurance);
  const lines = [
    `Verdict: ${v.word} (${result.verdict}${result.assurance ? `, ${result.assurance}` : ""}). Risk score ${result.risk_score}/100, confidence ${Math.round((result.confidence ?? 0) * 100)}%.`,
    ...(result.reasons || []).slice(0, 4).map((r) => `- ${r}`),
  ];
  for (const u of (result.urls || []).slice(0, 3)) {
    lines.push(`Link ${defang(u.url)}: ${u.verdict}, ${u.trust?.tier?.toLowerCase()} site${u.domain_age_days != null ? `, ${u.domain_age_days} days old` : ""}.`);
  }
  if (result.qr?.summary?.payee) lines.push(`UPI payee: ${result.qr.summary.payee}.`);
  lines.push(`Advice shown: ${result.recommendation}`);
  return lines.join("\n").slice(0, 1900);
}

/** Streams the assistant's reply, calling onText with each piece. */
export async function askAssistant(messages, context, { onText, signal }) {
  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      messages: messages.slice(-10).map((m) => ({ role: m.role, text: m.text.slice(0, 1200) })),
      context: context || null,
    }),
    signal,
  });
  if (response.status === 429) throw new Error("You're asking quickly. Please wait a moment and try again.");
  if (!response.ok) {
    let detail = "The assistant isn't available right now.";
    try {
      const body = await response.json();
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      /* keep default */
    }
    throw new Error(detail);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let failure = null;
  const feed = createSseParser(({ event, data }) => {
    if (event === "error") failure = data.message || "The assistant is busy right now.";
    else if (event === "message" && data.t) onText(data.t);
  });
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    feed(decoder.decode(value, { stream: true }));
  }
  if (failure) throw new Error(failure);
}
