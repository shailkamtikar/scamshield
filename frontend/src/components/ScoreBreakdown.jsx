import { useState } from "react";
import { getRiskConfig } from "../lib/risk";

/**
 * Renders the REAL score_breakdown the deterministic backend risk engine
 * returned — every row and the total come directly from the API response.
 * Nothing here is computed or guessed on the frontend.
 */
export default function ScoreBreakdown({ breakdown, riskScore, riskLevel }) {
  const [open, setOpen] = useState(false);

  if (!breakdown || breakdown.length === 0) return null;

  const risk = getRiskConfig(riskLevel);
  const total = breakdown.reduce((sum, item) => sum + item.points, 0);
  const maxPoints = Math.max(...breakdown.map((item) => item.points), 1);

  return (
    <section className="overflow-hidden rounded-2xl bg-surface shadow-[var(--shadow-card)]">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-5 py-4 text-left transition-colors hover:bg-surface-high/60"
      >
        <div className="flex items-center gap-3">
          <span className="material-symbols-outlined text-[20px] text-accent">calculate</span>
          <div>
            <span className="block text-[15px] font-medium text-text">Why this score?</span>
            <span className="font-mono text-[12px] text-text-muted">
              {breakdown.length} contributing signal{breakdown.length === 1 ? "" : "s"}
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
        <div className="flex flex-col gap-2.5 border-t border-border px-5 py-4">
          {breakdown.map((item, i) => (
            <div key={i} className="flex items-center gap-3">
              <span className="w-40 shrink-0 truncate text-[13px] text-text sm:w-56">
                {item.signal}
              </span>
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-surface-inset">
                <div
                  className={`h-full rounded-full ${risk.dot}`}
                  style={{ width: `${(item.points / maxPoints) * 100}%` }}
                />
              </div>
              <span className="w-12 shrink-0 text-right font-mono text-[13px] font-medium text-text">
                +{item.points}
              </span>
            </div>
          ))}

          <div className="mt-1 flex items-center justify-between border-t border-border pt-3">
            <span className="text-[13px] font-semibold text-text">Total</span>
            <span className={`font-mono text-[14px] font-semibold ${risk.text}`}>
              {Math.min(total, 100)} / 100
            </span>
          </div>
          {total > riskScore && (
            <p className="text-[11px] text-text-faint">
              Raw signal total ({total}) is capped at 100 for the final risk score.
            </p>
          )}
        </div>
      )}
    </section>
  );
}
