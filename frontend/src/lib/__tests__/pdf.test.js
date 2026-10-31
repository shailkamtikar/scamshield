import { describe, expect, it } from "vitest";
import { buildReportPdf } from "../pdf";

const link = {
  url: "http://sbi-kyc-update.top/login",
  verdict: "DANGEROUS",
  score: 90,
  trust: { tier: "UNKNOWN", brand: null },
  domain_age_days: 3,
  page_title: "SBI Login",
  reachability: { outcome: "OK", status: 200, chain: ["a", "b"] },
  reputation: [{ provider: "OpenPhish", status: "hit" }],
  sandbox: { source: "earlier_scan", malicious: true },
  destination: null,
};

function meta(overrides = {}) {
  return {
    mode: "text",
    ref: "SS-TEST",
    at: new Date("2026-11-01T10:00:00Z"),
    latencyMs: 2100,
    input: { message: "Your SBI account is blocked" },
    result: {
      verdict: "DANGEROUS",
      assurance: null,
      risk_score: 92,
      risk_level: "CRITICAL",
      confidence: 0.93,
      confidence_factors: { coverage: 0.9, agreement: 1 },
      reasoning_model: "gemini",
      weights_version: "2.0",
      reasons: ["The domain imitates SBI."],
      recommendation: "Do not open the link.",
      urls: [link],
      score_breakdown: [{ signal: "Lookalike", points: 60 }],
      evidence: Array.from({ length: 120 }, (_, i) => `Evidence line ${i}`),
      ...overrides,
    },
  };
}

describe("PDF report", () => {
  it("builds a multi-page report with long evidence and defanged links", () => {
    const doc = buildReportPdf(meta());
    expect(doc.getNumberOfPages()).toBeGreaterThan(1);
    const text = doc.output();
    expect(text).toContain("Dangerous");
    expect(text).not.toContain("http://sbi-kyc-update.top");
  });

  it("handles a dead link and a UPI QR with missing optional fields", () => {
    expect(buildReportPdf(meta({ verdict: "COULD_NOT_VERIFY", urls: [], score_breakdown: [], evidence: [] })).getNumberOfPages()).toBe(1);
    const qr = { summary: { payee: "Fresh Mart", vpa: "a@okaxis", amount: null } };
    const out = buildReportPdf({ ...meta({ verdict: "SAFE", assurance: "valid_payment", qr, decoded_text: "upi://pay", urls: [] }), mode: "qr" }).output();
    expect(out).toContain("Fresh Mart");
    expect(out).not.toContain("undefined");
  });
});
