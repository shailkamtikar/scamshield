import { motion } from "motion/react";
import { useEffect, useState } from "react";
import { MODE_CONFIG } from "../lib/modes";

function UtcClock() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  return <span>{now.toISOString().slice(11, 19)}Z</span>;
}

function RailItem({ label, children }) {
  return (
    <div className="border-b hairline py-4">
      <div className="label mb-1.5">{label}</div>
      <div className="font-mono text-[12px] text-text">{children}</div>
    </div>
  );
}

export function StatusDot({ health }) {
  const online = health?.status === "ok";
  const known = health !== undefined;
  const color = !known ? "bg-faint" : online ? "bg-safe" : "bg-danger";
  return (
    <span className="relative inline-flex h-2 w-2">
      {online && <span className="absolute inset-0 rounded-full bg-safe" style={{ animation: "pulse-ring 2s ease-out infinite" }} />}
      <span className={`relative h-2 w-2 rounded-full ${color}`} />
    </span>
  );
}

export function Header({ health, onHome }) {
  const online = health?.status === "ok";
  return (
    <header className="fixed inset-x-0 top-0 z-40 border-b hairline bg-ink/70 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-[1320px] items-center justify-between px-4 sm:px-6 lg:pl-[168px]">
        <button onClick={onHome} className="flex items-center gap-3" aria-label="ScamShield home">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden>
            <path d="M12 2 4 5.5v6c0 5 3.4 8.6 8 10.5 4.6-1.9 8-5.5 8-10.5v-6L12 2Z" stroke="rgb(var(--tint))" strokeWidth="1.6" />
            <path d="m8.5 12 2.5 2.5L15.5 9.5" stroke="rgb(var(--tint))" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <span className="display text-[22px] tracking-wide">ScamShield</span>
        </button>
        <div className="flex items-center gap-4">
          <span className="label hidden sm:inline">Free · No sign-up · Nothing stored</span>
          <span className="flex items-center gap-2 rounded-full border hairline px-3 py-1">
            <StatusDot health={health} />
            <span className="label !text-[10px]">{health === undefined ? "Checking" : online ? "Engine online" : "Engine offline"}</span>
          </span>
        </div>
      </div>
    </header>
  );
}

export function Rail({ health, mode, phase, stagesDone, stagesTotal }) {
  const providers = health?.providers ? Object.entries(health.providers) : [];
  const active = providers.filter(([, on]) => on).length;
  return (
    <aside className="fixed bottom-0 left-0 top-14 z-30 hidden w-[140px] border-r hairline px-5 lg:block">
      <RailItem label="Mode">{MODE_CONFIG[mode].no} / {MODE_CONFIG[mode].label}</RailItem>
      <RailItem label="State">
        <span className="tint-text">{phase === "idle" ? "Ready" : phase === "scanning" ? `Scanning ${stagesDone}/${stagesTotal || 5}` : phase === "result" ? "Report" : "Error"}</span>
      </RailItem>
      <RailItem label="Intel sources">
        {health ? `${active} / ${providers.length} live` : "—"}
      </RailItem>
      <RailItem label="Time"><UtcClock /></RailItem>
      <motion.div className="mt-6 h-px origin-left bg-[rgb(var(--tint))]" initial={{ scaleX: 0 }} animate={{ scaleX: 1 }} transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }} />
    </aside>
  );
}

export function Footer() {
  return (
    <footer className="border-t hairline px-4 py-8 sm:px-6 lg:pl-[168px]">
      <div className="mx-auto flex max-w-[1320px] flex-col gap-2 text-[12px] text-faint sm:flex-row sm:justify-between">
        <span>ScamShield is an automated assessment, not a guarantee. If you lost money, call <b className="text-muted">1930</b> or report at cybercrime.gov.in.</span>
        <span className="font-mono">Messages are analysed in memory and not stored.</span>
      </div>
    </footer>
  );
}
