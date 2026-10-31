import { AnimatePresence, motion } from "motion/react";
import { Check } from "lucide-react";
import { MODE_CONFIG } from "../lib/modes";

const EASE = [0.16, 1, 0.3, 1];

function Spinner() {
  return (
    <span className="relative inline-flex h-4 w-4">
      <span className="absolute inset-0 rounded-full border border-[rgba(var(--tint),0.25)]" />
      <motion.span className="absolute inset-0 rounded-full border-2 border-transparent border-t-[rgb(var(--tint))]" animate={{ rotate: 360 }} transition={{ duration: 0.8, repeat: Infinity, ease: "linear" }} />
    </span>
  );
}

const tone = (v) => `var(--color-${v === "SAFE" ? "safe" : v === "DANGEROUS" ? "danger" : v === "SUSPICIOUS" ? "warn" : "unknown"})`;

export default function ScanTimeline({ mode, stages, partialUrls, onCancel }) {
  const done = stages.filter((s) => s.status === "done").length;
  const pct = Math.min(96, (done / 5) * 100 + 6);
  return (
    <motion.section className="mx-auto w-full max-w-[760px] px-5 pb-24 pt-[120px] sm:px-0 sm:pt-[140px]" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.6, ease: EASE }} aria-live="polite">
      <span className="eyebrow">Investigating · {MODE_CONFIG[mode].label}</span>
      <h2 className="display mt-4 text-[clamp(2.4rem,6vw,4rem)]">Looking closely<span className="tint-text">…</span></h2>
      <p className="mt-3 max-w-[48ch] text-[15.5px] text-muted">Following the link without opening it on your device, checking threat lists and reading the wording.</p>

      <div className="surface mt-8 overflow-hidden">
        <div className="relative h-[3px] bg-line">
          <motion.div className="absolute inset-y-0 left-0 bg-[rgb(var(--tint))] shadow-[0_0_14px_rgba(var(--tint),0.8)]" animate={{ width: `${pct}%` }} transition={{ duration: 0.8, ease: EASE }} />
        </div>
        <ol className="divide-y divide-line">
          <AnimatePresence initial={false}>
            {stages.map((s) => (
              <motion.li key={s.id} layout initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.5, ease: EASE }} className="flex items-start gap-4 px-5 py-4">
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
                  <div className={`text-[15px] ${s.status === "done" ? "text-muted" : "text-text"}`}>{s.label}</div>
                  {s.detail && <div className="mt-0.5 truncate font-mono text-[11.5px] text-faint">{s.detail}</div>}
                </div>
              </motion.li>
            ))}
          </AnimatePresence>
          {stages.length === 0 && (
            <li className="flex items-center gap-4 px-5 py-4"><Spinner /><span className="text-[15px] text-muted">Starting the check…</span></li>
          )}
        </ol>
      </div>

      {partialUrls.length > 0 && (
        <motion.div className="mt-4 flex flex-wrap gap-2" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          {partialUrls.map((u) => (
            <span key={u.url} className="rounded-full border border-line-strong px-3 py-1.5 font-mono text-[11.5px] text-muted">
              {u.registrable} <b className="font-medium" style={{ color: tone(u.verdict) }}>{u.verdict.replaceAll("_", " ").toLowerCase()}</b>
            </span>
          ))}
        </motion.div>
      )}

      <button type="button" onClick={onCancel} className="btn-ghost mt-6 !py-2 !text-[13px]">Cancel</button>
    </motion.section>
  );
}
