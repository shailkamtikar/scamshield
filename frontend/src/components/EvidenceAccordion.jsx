import { useState } from "react";
import { classifyEvidence, EVIDENCE_TONE_CLASSES } from "../lib/evidence";

export default function EvidenceAccordion({ evidence }) {
  const [open, setOpen] = useState(true);

  if (!evidence || evidence.length === 0) {
    return (
      <section className="rounded-2xl bg-surface p-5 shadow-[var(--shadow-card)]">
        <div className="flex items-center gap-3">
          <span className="material-symbols-outlined text-[20px] text-text-muted">terminal</span>
          <div>
            <h3 className="text-[15px] font-medium text-text">Technical Evidence</h3>
            <p className="text-[12px] text-text-muted">
              No investigation evidence was recorded for this content.
            </p>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="overflow-hidden rounded-2xl bg-surface shadow-[var(--shadow-card)]">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-5 py-4 text-left transition-colors hover:bg-surface-high/60"
      >
        <div className="flex items-center gap-3">
          <span className="material-symbols-outlined text-[20px] text-accent">terminal</span>
          <div>
            <span className="block text-[15px] font-medium text-text">Technical Evidence</span>
            <span className="font-mono text-[12px] text-text-muted">
              {evidence.length} investigation signal{evidence.length === 1 ? "" : "s"} captured
            </span>
          </div>
        </div>
        <span
          className={`material-symbols-outlined text-text-muted transition-transform duration-200 ${
            open ? "rotate-180" : ""
          }`}
        >
          expand_more
        </span>
      </button>

      {open && (
        <div className="flex flex-col gap-2 bg-surface-inset/60 p-3">
          {evidence.map((item, i) => {
            const { badge, icon, tone } = classifyEvidence(item);
            const toneClass = EVIDENCE_TONE_CLASSES[tone] || EVIDENCE_TONE_CLASSES.neutral;
            return (
              <div
                key={i}
                className="flex flex-col gap-1.5 rounded-lg bg-surface p-3 sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="flex min-w-0 items-start gap-2">
                  <span className={`material-symbols-outlined mt-0.5 shrink-0 text-[16px] ${toneClass}`}>
                    {icon}
                  </span>
                  <span className="break-words font-mono text-[12.5px] leading-relaxed text-text">{item}</span>
                </div>
                <span
                  className={`shrink-0 self-start rounded bg-surface-high px-1.5 py-0.5 font-mono text-[10px] font-semibold tracking-wide ${toneClass} sm:self-center`}
                >
                  {badge}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}
