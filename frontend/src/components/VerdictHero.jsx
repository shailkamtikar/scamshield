import { getRiskConfig } from "../lib/risk";

const CIRCUMFERENCE = 2 * Math.PI * 30;

function ScoreGauge({ score, colorClass }) {
  const clamped = Math.max(0, Math.min(100, score));
  const offset = CIRCUMFERENCE * (1 - clamped / 100);

  return (
    <div className="relative flex h-20 w-20 shrink-0 items-center justify-center">
      <svg viewBox="0 0 72 72" className="h-full w-full -rotate-90">
        <circle cx="36" cy="36" r="30" fill="transparent" strokeWidth="6" className="stroke-surface-high" />
        <circle
          cx="36"
          cy="36"
          r="30"
          fill="transparent"
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={offset}
          className={colorClass}
          style={{ stroke: "currentColor", transition: "stroke-dashoffset 0.6s ease" }}
        />
      </svg>
      <span className={`material-symbols-outlined absolute text-[22px] ${colorClass}`}>shield</span>
    </div>
  );
}

export default function VerdictHero({ result, claimedOrganization }) {
  const risk = getRiskConfig(result.risk_level);
  const confidencePct = Math.round(Math.max(0, Math.min(1, result.confidence)) * 100);

  return (
    <section className={`relative overflow-hidden rounded-2xl border ${risk.edge}/30 bg-surface p-5 shadow-[var(--shadow-card)] md:p-6`}>
      <div className={`pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full ${risk.bg} blur-3xl`} />

      <div className="relative z-10 flex flex-col gap-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className={`inline-flex items-center gap-1.5 rounded-full ${risk.bg} px-3 py-1 ${risk.text}`}>
            <span className="material-symbols-outlined text-[18px]" style={{ fontVariationSettings: "'FILL' 1" }}>
              {risk.icon}
            </span>
            <span className="text-[12px] font-semibold uppercase tracking-wide">{risk.label}</span>
          </div>
          {claimedOrganization && (
            <div className="flex items-center gap-1.5 text-[12px] text-text-muted">
              <span className="material-symbols-outlined text-[15px]">business</span>
              <span>
                Claimed org: <strong className="text-text">{claimedOrganization}</strong>
              </span>
            </div>
          )}
        </div>

        <div>
          <h1 className="font-display text-[1.5rem] font-semibold tracking-tight text-text md:text-[1.75rem]">
            {risk.headline}
          </h1>
          <p className="mt-1 text-[14px] leading-relaxed text-text-muted">{risk.description}</p>
        </div>

        <div className="mt-1 grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div className="flex items-center justify-between rounded-xl bg-surface-high p-4">
            <div className="flex flex-col">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">
                Risk Score
              </span>
              <div className="mt-1 flex items-baseline gap-1">
                <span className={`font-num font-display text-[2.25rem] font-semibold leading-none ${risk.text}`}>
                  {result.risk_score}
                </span>
                <span className="text-[13px] text-text-faint">/ 100</span>
              </div>
            </div>
            <ScoreGauge score={result.risk_score} colorClass={risk.text} />
          </div>

          <div className="flex items-center justify-between rounded-xl bg-surface-high p-4">
            <div className="flex flex-col">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">
                Confidence
              </span>
              <div className="mt-1 flex items-baseline gap-1">
                <span className="font-num font-display text-[2.25rem] font-semibold leading-none text-text">
                  {confidencePct}%
                </span>
              </div>
              <span className="mt-1 text-[12px] text-text-faint">AI assessment certainty</span>
            </div>
            <div className="flex h-20 w-20 shrink-0 flex-col items-center justify-center gap-1.5 rounded-xl bg-surface px-2">
              <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-inset">
                <div className="h-full rounded-full bg-accent" style={{ width: `${confidencePct}%` }} />
              </div>
              <span className="font-mono text-[10px] text-text-faint">GEMINI EVAL</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
