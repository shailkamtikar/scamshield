import { getRiskConfig } from "../lib/risk";

export default function RecommendationBanner({ recommendation, riskLevel }) {
  if (!recommendation) return null;
  const risk = getRiskConfig(riskLevel);

  return (
    <section className={`relative overflow-hidden rounded-2xl bg-surface p-5 shadow-[var(--shadow-card)] md:p-6`}>
      <div className={`absolute inset-y-0 left-0 w-1.5 ${risk.dot}`} />
      <div className="flex flex-col gap-3 pl-3 md:flex-row md:items-start">
        <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${risk.bg} ${risk.text}`}>
          <span className="material-symbols-outlined text-[24px]" style={{ fontVariationSettings: "'FILL' 1" }}>
            {risk.text === getRiskConfig("LOW").text ? "shield" : "lock"}
          </span>
        </div>
        <div className="min-w-0 flex-1">
          <span className={`text-[11px] font-semibold uppercase tracking-wider ${risk.text}`}>
            Recommended Action
          </span>
          <p className="mt-1.5 text-[15px] leading-relaxed text-text">{recommendation}</p>
        </div>
      </div>
    </section>
  );
}
