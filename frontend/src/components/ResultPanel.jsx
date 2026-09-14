import { useState } from "react";
import VerdictHero from "./VerdictHero";
import ReasonsGrid from "./ReasonsGrid";
import RecommendationBanner from "./RecommendationBanner";
import EvidenceAccordion from "./EvidenceAccordion";
import ScoreBreakdown from "./ScoreBreakdown";
import ReasoningEngine from "./ReasoningEngine";
import { getRiskConfig } from "../lib/risk";
import { MODES, MODE_CONFIG } from "../lib/modes";
import { generateSummaryPdf } from "../lib/pdf";

export default function ResultPanel({
  result,
  submission,
  mode,
  imagePreviewUrl,
  latencyMs,
  localRef,
  generatedAt,
  onReset,
}) {
  const [copied, setCopied] = useState(false);
  const risk = getRiskConfig(result.risk_level);

  function copySummary() {
    const lines = [
      `ScamShield assessment — ${risk.label} (${result.risk_score}/100, ${Math.round(
        result.confidence * 100
      )}% confidence)`,
      "",
      "Reasons:",
      ...(result.reasons || []).map((r) => `- ${r}`),
      "",
      `Recommendation: ${result.recommendation}`,
    ].join("\n");

    navigator.clipboard?.writeText(lines);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  function downloadPdf() {
    generateSummaryPdf({ result, submission, mode, localRef, generatedAt, latencyMs });
  }

  const showImagePreview = mode !== MODES.TEXT && imagePreviewUrl;
  const analyzedTextLabel =
    mode === MODES.QR_CODE ? "Decoded QR content" : mode === MODES.SMS_IMAGE ? "OCR-extracted text" : "Analyzed content";
  const analyzedText =
    mode === MODES.TEXT
      ? submission.message
      : mode === MODES.QR_CODE
      ? result.decoded_text
      : result.extracted_text;

  return (
    <div className="flex flex-col gap-5">
      {/* Meta strip — only real, locally-known/measured metadata. No fabricated forensic IDs. */}
      <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl bg-surface-inset px-4 py-2.5 font-mono text-[11px] text-text-muted">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          <span>
            Local Ref <span className="text-text">{localRef}</span>
          </span>
          <span className="text-text-faint">|</span>
          <span className="inline-flex items-center gap-1">
            <span className="material-symbols-outlined text-[13px]">{MODE_CONFIG[mode].icon}</span>
            {MODE_CONFIG[mode].label}
          </span>
        </div>
        <span>Response time: {latencyMs}ms</span>
      </div>

      {(showImagePreview || analyzedText) && (
        <div className="rounded-xl bg-surface-inset p-4">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">
            {analyzedTextLabel}
          </span>
          <div className="mt-2 flex flex-col gap-3 sm:flex-row sm:items-start">
            {showImagePreview && (
              <img
                src={imagePreviewUrl}
                alt="Uploaded content"
                className="h-24 w-24 shrink-0 rounded-lg border border-border bg-surface object-contain"
              />
            )}
            {analyzedText ? (
              <p className="line-clamp-4 min-w-0 flex-1 font-mono text-[12.5px] italic leading-relaxed text-text/90">
                &ldquo;{analyzedText}&rdquo;
              </p>
            ) : (
              <p className="min-w-0 flex-1 text-[12.5px] text-text-faint">
                No readable text was extracted from the uploaded image.
              </p>
            )}
          </div>
        </div>
      )}

      <VerdictHero result={result} claimedOrganization={submission.claimedOrganization} />
      <ScoreBreakdown
        breakdown={result.score_breakdown}
        riskScore={result.risk_score}
        riskLevel={result.risk_level}
      />
      <ReasonsGrid reasons={result.reasons} riskLevel={result.risk_level} />
      <RecommendationBanner recommendation={result.recommendation} riskLevel={result.risk_level} />
      <EvidenceAccordion evidence={result.evidence} />
      <ReasoningEngine reasoningModel={result.reasoning_model} />

      <div className="flex flex-col items-center justify-between gap-3 border-t border-border pt-5 sm:flex-row">
        <button
          type="button"
          onClick={onReset}
          className="inline-flex w-full items-center justify-center gap-1.5 rounded-lg bg-surface px-5 py-2.5 text-[14px] font-medium text-text shadow-[var(--shadow-card)] transition-colors hover:bg-surface-high sm:w-auto"
        >
          <span className="material-symbols-outlined text-[18px]">replay</span>
          Analyze another
        </button>
        <div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row">
          <button
            type="button"
            onClick={copySummary}
            className="inline-flex w-full items-center justify-center gap-1.5 rounded-lg bg-surface px-5 py-2.5 text-[14px] font-medium text-text shadow-[var(--shadow-card)] transition-colors hover:bg-surface-high sm:w-auto"
          >
            <span className="material-symbols-outlined text-[16px]">
              {copied ? "check" : "content_copy"}
            </span>
            {copied ? "Copied!" : "Copy Summary"}
          </button>
          <button
            type="button"
            onClick={downloadPdf}
            className="inline-flex w-full items-center justify-center gap-1.5 rounded-lg bg-accent px-5 py-2.5 text-[14px] font-semibold text-accent-fg transition-colors hover:bg-accent-hover sm:w-auto"
          >
            <span className="material-symbols-outlined text-[18px]">download</span>
            Download Summary Report
          </button>
        </div>
      </div>
    </div>
  );
}
