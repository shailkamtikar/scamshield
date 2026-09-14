import { getRiskConfig } from "../lib/risk";

export default function ReasonsGrid({ reasons, riskLevel }) {
  if (!reasons || reasons.length === 0) return null;
  const risk = getRiskConfig(riskLevel);

  return (
    <section>
      <div className="mb-3 flex flex-col">
        <span className="font-mono text-[11px] font-medium uppercase tracking-widest text-accent">
          AI Reasoning
        </span>
        <h2 className="mt-0.5 font-display text-[1.25rem] font-semibold tracking-tight text-text">
          Why this was flagged
        </h2>
        <p className="mt-0.5 text-[13px] text-text-muted">
          {reasons.length} reason{reasons.length === 1 ? "" : "s"} returned by ScamShield&apos;s AI assessment.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {reasons.map((reason, i) => (
          <div
            key={i}
            className="flex items-start gap-3 rounded-xl bg-surface p-4 shadow-[var(--shadow-card)]"
          >
            <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${risk.bg} ${risk.text}`}>
              <span className="material-symbols-outlined text-[18px]">{risk.icon}</span>
            </div>
            <p className="text-[14px] leading-relaxed text-text">{reason}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
