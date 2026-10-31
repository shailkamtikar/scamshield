import { AnimatePresence, motion } from "motion/react";
import { Check } from "lucide-react";

const EASE = [0.22, 1, 0.36, 1];

function Spinner() {
  return (
    <span className="relative inline-flex h-5 w-5">
      <span className="absolute inset-0 rounded-full border-2 border-line" />
      <motion.span className="absolute inset-0 rounded-full border-2 border-transparent border-t-brand" animate={{ rotate: 360 }} transition={{ duration: 0.9, repeat: Infinity, ease: "linear" }} />
    </span>
  );
}

export default function ScanTimeline({ stages, onCancel }) {
  const done = stages.filter((s) => s.status === "done").length;
  const total = Math.max(stages.some((s) => s.id === "read" || s.id === "decode") ? 6 : 5, stages.length);
  return (
    <motion.section className="mx-auto w-full max-w-[640px] pt-8 sm:pt-14" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.5, ease: EASE }} aria-live="polite">
      <h2 className="text-[30px] sm:text-[36px]">Checking this for you…</h2>
      <p className="mt-2 text-soft">This usually takes a few seconds. A careful look at an unknown site can take up to half a minute.</p>

      <div className="card mt-6 overflow-hidden">
        <div className="h-1 bg-sunken">
          <motion.div className="h-full bg-brand" animate={{ width: `${Math.min(100, (done / total) * 100 + 6)}%` }} transition={{ duration: 0.7, ease: EASE }} />
        </div>
        <ol className="divide-y divide-line">
          <AnimatePresence initial={false}>
            {stages.map((s) => (
              <motion.li key={s.id} layout initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4, ease: EASE }} className="flex items-start gap-3.5 px-5 py-3.5">
                <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center">
                  {s.status === "done" ? (
                    <motion.span initial={{ scale: 0.4, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ type: "spring", stiffness: 420, damping: 22 }} className="flex h-5 w-5 items-center justify-center rounded-full bg-brand text-on-brand">
                      <Check size={13} strokeWidth={3} />
                    </motion.span>
                  ) : (
                    <Spinner />
                  )}
                </span>
                <div className="min-w-0">
                  <p className={s.status === "done" ? "text-soft" : "font-medium"}>{s.label}</p>
                  {s.detail && <p className="truncate text-[14px] text-faint">{s.detail}</p>}
                </div>
              </motion.li>
            ))}
          </AnimatePresence>
          {stages.length === 0 && (
            <li className="flex items-center gap-3.5 px-5 py-3.5"><Spinner /><span className="text-soft">Getting started…</span></li>
          )}
        </ol>
      </div>

      <button type="button" onClick={onCancel} className="btn-quiet mt-5 !px-4 !py-2">Cancel</button>
    </motion.section>
  );
}
