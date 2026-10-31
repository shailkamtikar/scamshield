import { AnimatePresence, motion } from "motion/react";
import { Check } from "lucide-react";
import { MODE_CONFIG } from "../lib/modes";

function Spinner() {
  return (
    <span className="relative inline-flex h-4 w-4">
      <span className="absolute inset-0 rounded-full border border-[rgba(var(--tint),0.25)]" />
      <motion.span className="absolute inset-0 rounded-full border-2 border-transparent border-t-[rgb(var(--tint))]" animate={{ rotate: 360 }} transition={{ duration: 0.8, repeat: Infinity, ease: "linear" }} />
    </span>
  );
}

export default function ScanTimeline({ mode, stages, partialUrls, onCancel }) {
  const done = stages.filter((s) => s.status === "done").length;
  return (
    <motion.section className="mx-auto w-full max-w-[860px] pt-6 sm:pt-12" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }} aria-live="polite">
      <div className="label mb-3 flex items-center gap-3"><span className="inline-block h-px w-8 bg-[rgb(var(--tint))]" />Scanning · {MODE_CONFIG[mode].label}</div>
      <h2 className="display text-[clamp(2.6rem,9vw,6.5rem)]">Investigating<span className="tint-text">.</span></h2>

      <div className="mt-8 border hairline bg-ink-2/70 p-1">
        <div className="relative h-[3px] overflow-hidden bg-line">
          <motion.div className="absolute inset-y-0 left-0 bg-[rgb(var(--tint))]" animate={{ width: `${Math.min(100, (done / 5) * 100 + 8)}%` }} transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }} />
        </div>
        <ol className="divide-y divide-line">
          <AnimatePresence initial={false}>
            {stages.map((s) => (
              <motion.li key={s.id} layout initial={{ opacity: 0, x: -14 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }} className="flex items-start gap-4 px-5 py-4">
                <span className="mt-0.5 flex h-5 w-5 items-center justify-center">
                  {s.status === "done" ? (
                    <motion.span initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ type: "spring", stiffness: 500, damping: 18 }} className="flex h-5 w-5 items-center justify-center rounded-full bg-[rgb(var(--tint))] text-ink"><Check size={12} strokeWidth={3} /></motion.span>
                  ) : s.status === "failed" ? (
                    <span className="h-2 w-2 rounded-full bg-danger" />
                  ) : (
                    <Spinner />
                  )}
                </span>
                <div className="min-w-0 flex-1">
                  <div className={`text-[14px] ${s.status === "done" ? "text-muted" : "text-text"}`}>{s.label}</div>
                  {s.detail && <div className="mt-0.5 truncate font-mono text-[11px] text-faint">{s.detail}</div>}
                </div>
              </motion.li>
            ))}
          </AnimatePresence>
          {stages.length === 0 && (
            <li className="flex items-center gap-4 px-5 py-4"><Spinner /><span className="text-[14px] text-muted">Waking the engine…</span></li>
          )}
        </ol>
      </div>

      {partialUrls.length > 0 && (
        <motion.div className="mt-4 flex flex-wrap gap-2" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          {partialUrls.map((u) => (
            <span key={u.url} className="border hairline px-3 py-1.5 font-mono text-[11px] text-muted">{u.registrable} <b style={{ color: `var(--color-${u.verdict === "SAFE" ? "safe" : u.verdict === "DANGEROUS" ? "danger" : u.verdict === "SUSPICIOUS" ? "warn" : "unknown"})` }}>{u.verdict.replaceAll("_", " ")}</b></span>
          ))}
        </motion.div>
      )}

      <button type="button" onClick={onCancel} className="mt-6 border hairline px-4 py-2 text-[12px] text-muted transition-colors hover:text-text">Cancel</button>
    </motion.section>
  );
}
