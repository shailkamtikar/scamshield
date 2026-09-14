import { jsPDF } from "jspdf";
import { getRiskConfig } from "./risk";
import { formatModelName } from "./reasoningModel";
import { MODE_CONFIG } from "./modes";

const PAGE_MARGIN = 48;
const PAGE_WIDTH = 595.28; // A4 pt
const PAGE_HEIGHT = 841.89; // A4 pt
const CONTENT_WIDTH = PAGE_WIDTH - PAGE_MARGIN * 2;

// Always black-on-white and independent of the app's current theme, so the
// report stays readable when printed in black & white.
const INK = "#0f172a";
const MUTED = "#475569";
const RULE = "#cbd5e1";

function newCursor() {
  return { y: PAGE_MARGIN };
}

function ensureSpace(doc, cursor, needed) {
  if (cursor.y + needed > PAGE_HEIGHT - PAGE_MARGIN) {
    doc.addPage();
    cursor.y = PAGE_MARGIN;
  }
}

function drawSectionHeading(doc, cursor, text) {
  ensureSpace(doc, cursor, 26);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(11);
  doc.setTextColor(INK);
  doc.text(text.toUpperCase(), PAGE_MARGIN, cursor.y);
  cursor.y += 6;
  doc.setDrawColor(RULE);
  doc.setLineWidth(0.75);
  doc.line(PAGE_MARGIN, cursor.y, PAGE_WIDTH - PAGE_MARGIN, cursor.y);
  cursor.y += 16;
}

function drawKeyValueRow(doc, cursor, label, value, valueOffset = 130) {
  if (!value) return;
  ensureSpace(doc, cursor, 16);
  doc.setFont("helvetica", "bold");
  doc.setFontSize(9.5);
  doc.setTextColor(MUTED);
  const labelLines = doc.splitTextToSize(label.toUpperCase(), valueOffset - 10);
  doc.text(labelLines, PAGE_MARGIN, cursor.y);

  doc.setFont("helvetica", "normal");
  doc.setFontSize(10.5);
  doc.setTextColor(INK);
  const lines = doc.splitTextToSize(String(value), CONTENT_WIDTH - valueOffset);
  doc.text(lines, PAGE_MARGIN + valueOffset, cursor.y);
  cursor.y += Math.max(14, lines.length * 13, labelLines.length * 12) + 4;
}

function drawParagraph(doc, cursor, text, { size = 10.5, color = INK, gap = 16 } = {}) {
  doc.setFont("helvetica", "normal");
  doc.setFontSize(size);
  doc.setTextColor(color);
  const lines = doc.splitTextToSize(text, CONTENT_WIDTH);
  ensureSpace(doc, cursor, lines.length * (size + 3.5) + gap);
  doc.text(lines, PAGE_MARGIN, cursor.y);
  cursor.y += lines.length * (size + 3.5) + gap;
}

function drawBulletList(doc, cursor, items) {
  doc.setFont("helvetica", "normal");
  doc.setFontSize(10.5);
  doc.setTextColor(INK);

  for (const item of items) {
    const lines = doc.splitTextToSize(item, CONTENT_WIDTH - 16);
    ensureSpace(doc, cursor, lines.length * 14 + 6);
    doc.setFillColor(INK);
    doc.circle(PAGE_MARGIN + 3, cursor.y - 3, 1.4, "F");
    doc.text(lines, PAGE_MARGIN + 14, cursor.y);
    cursor.y += lines.length * 14 + 6;
  }
}

/**
 * Builds a print-friendly PDF summary from the CURRENT investigation
 * result only — every value below is read from the real API response and
 * the real submission the user made. Nothing here is hardcoded.
 */
export function generateSummaryPdf({ result, submission, mode, localRef, generatedAt, latencyMs }) {
  const doc = new jsPDF({ unit: "pt", format: "a4" });
  const cursor = newCursor();
  const risk = getRiskConfig(result.risk_level);

  // Title block
  doc.setFont("helvetica", "bold");
  doc.setFontSize(20);
  doc.setTextColor(INK);
  doc.text("SCAMSHIELD", PAGE_MARGIN, cursor.y);
  cursor.y += 20;

  doc.setFont("helvetica", "normal");
  doc.setFontSize(12);
  doc.setTextColor(MUTED);
  doc.text("Scam & Phishing Investigation Summary", PAGE_MARGIN, cursor.y);
  cursor.y += 18;

  doc.setDrawColor(RULE);
  doc.setLineWidth(1);
  doc.line(PAGE_MARGIN, cursor.y, PAGE_WIDTH - PAGE_MARGIN, cursor.y);
  cursor.y += 26;

  // INVESTIGATION
  drawSectionHeading(doc, cursor, "Investigation");
  drawKeyValueRow(doc, cursor, "Local Reference", localRef);
  drawKeyValueRow(doc, cursor, "Generated", generatedAt.toLocaleString());
  drawKeyValueRow(doc, cursor, "Input Mode", MODE_CONFIG[mode]?.label || mode);
  drawKeyValueRow(doc, cursor, "Claimed Organization", submission.claimedOrganization || "Not provided");
  if (latencyMs != null) drawKeyValueRow(doc, cursor, "Backend Response Time", `${latencyMs} ms`);
  if (result.reasoning_model) {
    drawKeyValueRow(doc, cursor, "Reasoning Engine", formatModelName(result.reasoning_model));
  }
  cursor.y += 6;

  // Analyzed content
  const analyzedText =
    mode === "text"
      ? submission.message
      : mode === "qr_code"
      ? result.decoded_text
        ? `Decoded QR content: ${result.decoded_text}`
        : null
      : result.extracted_text
      ? `OCR-extracted text: ${result.extracted_text}`
      : "No readable text was extracted from the uploaded image.";

  if (analyzedText) {
    drawSectionHeading(doc, cursor, "Analyzed Content");
    drawParagraph(doc, cursor, analyzedText, { size: 9.5, color: MUTED });
  }

  // VERDICT
  drawSectionHeading(doc, cursor, "Verdict");
  drawKeyValueRow(doc, cursor, "Risk Level", risk.label.toUpperCase());
  drawKeyValueRow(doc, cursor, "Risk Score", `${result.risk_score} / 100`);
  drawKeyValueRow(
    doc,
    cursor,
    "Confidence",
    `${Math.round(Math.max(0, Math.min(1, result.confidence)) * 100)}%`
  );
  cursor.y += 6;

  // WHY THIS SCORE? — the real deterministic score_breakdown from the API.
  if (result.score_breakdown?.length) {
    drawSectionHeading(doc, cursor, "Why This Score?");
    for (const item of result.score_breakdown) {
      drawKeyValueRow(doc, cursor, item.signal, `+${item.points}`, 260);
    }
    ensureSpace(doc, cursor, 20);
    doc.setDrawColor(RULE);
    doc.setLineWidth(0.5);
    doc.line(PAGE_MARGIN, cursor.y, PAGE_MARGIN + 260, cursor.y);
    cursor.y += 12;
    drawKeyValueRow(doc, cursor, "Total", `${result.risk_score} / 100`, 260);
    cursor.y += 6;
  }

  // WHY THIS WAS FLAGGED
  if (result.reasons?.length) {
    drawSectionHeading(doc, cursor, "Why This Was Flagged");
    drawBulletList(doc, cursor, result.reasons);
    cursor.y += 6;
  }

  // RECOMMENDED ACTION
  if (result.recommendation) {
    drawSectionHeading(doc, cursor, "Recommended Action");
    drawParagraph(doc, cursor, result.recommendation);
  }

  // TECHNICAL EVIDENCE
  if (result.evidence?.length) {
    drawSectionHeading(doc, cursor, "Technical Evidence");
    drawBulletList(doc, cursor, result.evidence);
  }

  // Footer disclaimer on every page
  const pageCount = doc.getNumberOfPages();
  for (let i = 1; i <= pageCount; i++) {
    doc.setPage(i);
    doc.setFont("helvetica", "normal");
    doc.setFontSize(8);
    doc.setTextColor(MUTED);
    doc.text(
      "Generated locally by the ScamShield web app from a live backend investigation. Not stored on any server.",
      PAGE_MARGIN,
      PAGE_HEIGHT - 28
    );
    doc.text(`Page ${i} of ${pageCount}`, PAGE_WIDTH - PAGE_MARGIN - 60, PAGE_HEIGHT - 28);
  }

  doc.save(`scamshield-report-${localRef}.pdf`);
}
