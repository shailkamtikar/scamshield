import { useEffect, useState } from "react";
import { MODES, MODE_CONFIG } from "../lib/modes";

// Purely a visual pacing device. The backend performs ONE request through the
// whole LangGraph pipeline and returns a single response — these stages are
// not individually streamed from the server. They just give the user a sense
// of what ScamShield's pipeline actually does while the one request is in flight.
function stagesFor(mode) {
  const firstStage = MODE_CONFIG[mode].firstStage;
  return [
    firstStage,
    "Checking URL signals",
    "Checking impersonation signals",
    "Analyzing social-engineering patterns",
    "Running AI reasoning",
    "Preparing assessment",
  ];
}

const STAGE_INTERVAL_MS = 800;

export default function LoadingPanel({ mode = MODES.TEXT }) {
  const stages = stagesFor(mode);
  const [activeIndex, setActiveIndex] = useState(0);

  useEffect(() => {
    if (activeIndex >= stages.length - 1) return;
    const timer = setTimeout(() => setActiveIndex((i) => i + 1), STAGE_INTERVAL_MS);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeIndex]);

  return (
    <section className="rounded-2xl border border-border bg-surface p-6 shadow-[var(--shadow-card)] md:p-8">
      <div className="flex flex-col items-center gap-1 pb-6 text-center">
        <div className="mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-accent/10 text-accent">
          <span className="material-symbols-outlined animate-shield-pulse text-[26px]">shield_with_heart</span>
        </div>
        <h2 className="font-display text-[1.25rem] font-semibold text-text">
          {MODE_CONFIG[mode].loadingHeadline}
        </h2>
        <p className="text-[13px] text-text-muted">
          ScamShield is running your content through its investigation pipeline.
        </p>
      </div>

      <ul className="mx-auto flex max-w-[380px] flex-col gap-3">
        {stages.map((stage, i) => {
          const done = i < activeIndex;
          const active = i === activeIndex;
          return (
            <li key={stage} className="flex items-center gap-3">
              <span
                className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full border text-[14px] transition-colors ${
                  done
                    ? "border-positive bg-positive-bg text-positive"
                    : active
                    ? "border-accent text-accent"
                    : "border-border text-text-faint"
                }`}
              >
                {done ? (
                  <span className="material-symbols-outlined text-[14px]">check</span>
                ) : active ? (
                  <span className="block h-2 w-2 animate-pulse rounded-full bg-accent" />
                ) : (
                  ""
                )}
              </span>
              <span
                className={`text-[14px] transition-colors ${
                  done || active ? "text-text" : "text-text-faint"
                }`}
              >
                {stage}
              </span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
