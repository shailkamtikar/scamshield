import { useState } from "react";
import ImageDropzone from "./ImageDropzone";
import { MODES, MODE_CONFIG } from "../lib/modes";

const DEMO_MESSAGE =
  "URGENT! Your Microsoft account has been suspended. Click here: https://miconsoft-login.com Call 9998269178 immediately.";

export default function AnalyzeForm({ mode, onModeChange, onSubmit, disabled }) {
  const [message, setMessage] = useState("");
  const [claimedOrganization, setClaimedOrganization] = useState("");
  const [file, setFile] = useState(null);

  const trimmedMessage = message.trim();
  const canSubmit =
    !disabled && (mode === MODES.TEXT ? trimmedMessage.length > 0 : Boolean(file));

  function handleSubmit(e) {
    e.preventDefault();
    if (!canSubmit) return;

    if (mode === MODES.TEXT) {
      onSubmit({ mode, message: trimmedMessage, claimedOrganization: claimedOrganization.trim() });
    } else {
      onSubmit({ mode, file, claimedOrganization: claimedOrganization.trim() });
    }
  }

  function fillDemoExample() {
    onModeChange(MODES.TEXT);
    setMessage(DEMO_MESSAGE);
    setClaimedOrganization("Microsoft");
  }

  function handleModeChange(nextMode) {
    setFile(null);
    onModeChange(nextMode);
  }

  return (
    <section className="rounded-2xl border border-border bg-surface shadow-[var(--shadow-card)]">
      <form onSubmit={handleSubmit} className="flex flex-col gap-5 p-5 md:p-6">
        <div className="flex flex-wrap items-center gap-1.5">
          {Object.values(MODES).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => handleModeChange(m)}
              className={`inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[13px] font-medium transition-colors ${
                mode === m
                  ? "bg-surface-high text-text"
                  : "text-text-muted hover:bg-surface-high/60 hover:text-text"
              }`}
            >
              <span className="material-symbols-outlined text-[16px]">
                {MODE_CONFIG[m].icon}
              </span>
              {MODE_CONFIG[m].label}
            </button>
          ))}
        </div>

        {mode === MODES.TEXT && (
          <div className="rounded-xl border border-border bg-surface-inset p-1 focus-within:border-accent focus-within:ring-1 focus-within:ring-accent">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Paste a suspicious SMS or message here..."
              rows={6}
              className="w-full resize-y rounded-lg bg-transparent p-3 text-[15px] leading-relaxed text-text placeholder:text-text-faint focus:outline-none"
            />
            <div className="flex items-center justify-between px-3 pb-2 pt-1">
              <span className="font-mono text-[11px] text-text-faint">
                {message.length.toLocaleString()} characters
              </span>
              <button
                type="button"
                onClick={fillDemoExample}
                className="font-mono text-[11px] text-accent hover:text-accent-hover"
              >
                Use demo example
              </button>
            </div>
          </div>
        )}

        {mode === MODES.SMS_IMAGE && (
          <ImageDropzone
            file={file}
            onFileSelect={setFile}
            onRemove={() => setFile(null)}
            icon="upload"
            title="Upload SMS screenshot"
            subtitle="Drag and drop, or click to browse"
          />
        )}

        {mode === MODES.QR_CODE && (
          <ImageDropzone
            file={file}
            onFileSelect={setFile}
            onRemove={() => setFile(null)}
            icon="qr_code_2"
            title="Upload QR code image"
            subtitle="Drag and drop, or click to browse"
          />
        )}

        <label className="flex flex-col gap-1.5">
          <span className="text-[13px] font-medium text-text-muted">
            Claimed organization <span className="text-text-faint">(optional)</span>
          </span>
          <input
            type="text"
            value={claimedOrganization}
            onChange={(e) => setClaimedOrganization(e.target.value)}
            placeholder="e.g. Microsoft, Google, SBI..."
            className="rounded-lg border border-border bg-surface-inset px-3 py-2.5 text-[14px] text-text placeholder:text-text-faint focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          />
        </label>

        <button
          type="submit"
          disabled={!canSubmit}
          className="mt-1 inline-flex items-center justify-center gap-2 rounded-lg bg-accent px-5 py-3 text-[14px] font-semibold text-accent-fg shadow-[inset_0_1px_0_rgba(255,255,255,0.15)] transition-colors hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-40"
        >
          <span className="material-symbols-outlined text-[18px]">shield_with_heart</span>
          Analyze with ScamShield
        </button>
      </form>
    </section>
  );
}
