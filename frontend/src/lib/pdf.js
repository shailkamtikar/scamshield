import { jsPDF } from "jspdf";
import { MODE_CONFIG } from "./modes";
import { getVerdict } from "./verdict";
import { defang } from "./format";

const M = 48;
const W = 595.28;
const H = 841.89;
const CW = W - M * 2;
const INK = "#0f172a";
const MUTED = "#475569";
const RULE = "#cbd5e1";

/** Black-on-white, printable report built only from the real API response. */
export function buildReportPdf(meta) {
  const { result, mode, ref, at, latencyMs, input } = meta;
  const v = getVerdict(result.verdict, result.assurance);
  const doc = new jsPDF({ unit: "pt", format: "a4" });
  const cur = { y: M };

  const need = (n) => {
    if (cur.y + n > H - M - 20) {
      doc.addPage();
      cur.y = M;
    }
  };
  const heading = (t) => {
    need(36);
    cur.y += 8;
    doc.setFont("helvetica", "bold").setFontSize(11).setTextColor(INK).text(t.toUpperCase(), M, cur.y);
    cur.y += 6;
    doc.setDrawColor(RULE).setLineWidth(0.75).line(M, cur.y, W - M, cur.y);
    cur.y += 16;
  };
  const para = (t, { size = 10.5, color = INK, font = "normal", gap = 8 } = {}) => {
    doc.setFont("helvetica", font).setFontSize(size).setTextColor(color);
    const lines = doc.splitTextToSize(String(t), CW);
    need(lines.length * (size + 3.5) + gap);
    doc.text(lines, M, cur.y);
    cur.y += lines.length * (size + 3.5) + gap;
  };
  const row = (k, val) => {
    if (val == null || val === "") return;
    doc.setFont("helvetica", "bold").setFontSize(9).setTextColor(MUTED);
    const lines = doc.splitTextToSize(String(val), CW - 140);
    need(Math.max(14, lines.length * 13) + 4);
    doc.text(k.toUpperCase(), M, cur.y);
    doc.setFont("helvetica", "normal").setFontSize(10.5).setTextColor(INK).text(lines, M + 140, cur.y);
    cur.y += Math.max(14, lines.length * 13) + 4;
  };
  const bullets = (items) => {
    for (const item of items) {
      doc.setFont("helvetica", "normal").setFontSize(10.5).setTextColor(INK);
      const lines = doc.splitTextToSize(String(item), CW - 16);
      need(lines.length * 14 + 6);
      doc.setFillColor(INK).circle(M + 3, cur.y - 3, 1.4, "F");
      doc.text(lines, M + 14, cur.y);
      cur.y += lines.length * 14 + 6;
    }
  };

  doc.setFont("helvetica", "bold").setFontSize(20).setTextColor(INK).text("SCAMSHIELD", M, cur.y);
  cur.y += 18;
  doc.setFont("helvetica", "normal").setFontSize(12).setTextColor(MUTED).text("Scam & phishing investigation report", M, cur.y);
  cur.y += 12;
  doc.setDrawColor(INK).setLineWidth(1.2).line(M, cur.y, W - M, cur.y);
  cur.y += 8;

  heading("Verdict");
  doc.setFont("helvetica", "bold").setFontSize(26).setTextColor(INK).text(v.word.toUpperCase(), M, cur.y + 8);
  cur.y += 26;
  para(`${v.headline} ${v.blurb}`, { color: MUTED });
  if (result.verdict !== "COULD_NOT_VERIFY") row("Risk score", `${result.risk_score} / 100`);
  row("Risk level", result.risk_level);
  row("Confidence", `${Math.round(result.confidence * 100)}%  (${Math.round((result.confidence_factors?.coverage ?? 0) * 100)}% of checks completed, ${Math.round((result.confidence_factors?.agreement ?? 0) * 100)}% of strong evidence agrees)`);

  heading("Investigation");
  row("Reference", ref);
  row("Generated", at.toLocaleString());
  row("Input type", MODE_CONFIG[mode].label);
  row("Response time", `${(latencyMs / 1000).toFixed(1)} s`);
  row("Explanation by", result.reasoning_model || "built-in rules");
  row("Engine", `scoring weights v${result.weights_version}`);

  const content = mode === "text" ? input.message : result.extracted_text || result.decoded_text;
  if (content) {
    heading(mode === "text" ? "Message analysed" : mode === "qr" ? "QR content" : "Text read from screenshot");
    para(content, { size: 9.5, color: MUTED });
  }

  heading("Why this verdict");
  bullets(result.reasons);

  if (result.qr?.summary) {
    heading("Payment details in the QR");
    const s = result.qr.summary;
    row("Payee", s.payee);
    row("UPI address", s.vpa);
    row("Amount", s.amount ? `INR ${s.amount}` : "Not preset");
    row("Note", s.note);
  }

  if (result.urls.length) {
    heading("Links inspected");
    result.urls.forEach((u, i) => {
      need(60);
      para(`${i + 1}. ${defang(u.url)}`, { font: "bold", gap: 4 });
      row("Verdict", `${getVerdict(u.verdict, u.trust.tier === "UNKNOWN" ? "no_problems_found" : "verified").word}${u.score != null ? ` (score ${u.score})` : ""}`);
      row("Trust", u.trust.brand ? `${u.trust.tier} - ${u.trust.brand}` : u.trust.tier);
      if (u.domain_age_days != null) row("Domain age", `${u.domain_age_days} days`);
      if (u.reachability) row("Reachability", `${u.reachability.outcome}${u.reachability.status ? ` (${u.reachability.status})` : ""}, ${Math.max(0, (u.reachability.chain?.length || 1) - 1)} redirect(s)`);
      if (u.reputation?.length) row("Threat feeds", u.reputation.map((p) => `${p.provider}: ${p.status}`).join("; "));
      if (u.page_title) row("Page title", u.page_title);
      if (u.sandbox) row("Sandbox", `${u.sandbox.source === "live_scan" ? "Live scan" : "Earlier scan"} by urlscan.io${u.sandbox.malicious === true ? ": judged malicious" : ""}`);
      if (u.destination) row("Final destination", defang(u.destination.url));
      cur.y += 6;
    });
  }

  if (result.score_breakdown?.length) {
    heading("Score breakdown");
    result.score_breakdown.forEach((r) => row(r.signal, `${r.points > 0 ? "+" : ""}${r.points}`));
  }

  heading("What to do next");
  para(result.recommendation);
  if (result.verdict !== "SAFE") para("Report cyber fraud at cybercrime.gov.in or call helpline 1930.", { color: MUTED });

  heading("Technical evidence");
  bullets(result.evidence);

  const pages = doc.getNumberOfPages();
  for (let i = 1; i <= pages; i++) {
    doc.setPage(i);
    doc.setFont("helvetica", "normal").setFontSize(8).setTextColor(MUTED);
    doc.text("Automated assessment, not a guarantee. Links are shown defanged. Generated locally; nothing is stored on a server.", M, H - 26);
    doc.text(`Page ${i} of ${pages}`, W - M - 56, H - 26);
  }
  return doc;
}

export function generateReportPdf(meta) {
  buildReportPdf(meta).save(`scamshield-${meta.ref}.pdf`);
}
