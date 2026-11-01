import { AnimatePresence, motion } from "motion/react";
import { ArrowRight, TriangleAlert } from "lucide-react";
import { useState } from "react";
import { EXAMPLES } from "../../data/scams";
import { EASE, FadeUp, SectionHead } from "../ui/Reveal";

export default function Examples({ onTry }) {
  const [id, setId] = useState(EXAMPLES[0].id);
  const [shown, setShown] = useState(0); // how many explanations are revealed
  const ex = EXAMPLES.find((e) => e.id === id);

  return (
    <section id="examples" className="relative border-t border-line bg-ink-2/40 px-5 py-24 sm:px-8 sm:py-32">
      <div className="mx-auto max-w-[1200px]">
        <div className="flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
          <SectionHead eyebrow="Real-world patterns" title="See what a scam looks like, line by line.">
            Four common scripts. Tap each flag to see why it is a warning sign.
          </SectionHead>
          <FadeUp className="text-[13px] text-faint lg:max-w-[260px] lg:text-right">These are illustrative examples written for this page. They are not detected threats.</FadeUp>
        </div>

        <FadeUp delay={0.1} className="mt-12">
          <div role="tablist" aria-label="Examples" className="mb-6 flex flex-wrap gap-2">
            {EXAMPLES.map((e) => (
              <button
                key={e.id} type="button" role="tab" aria-selected={id === e.id} onClick={() => { setId(e.id); setShown(0); }}
                className={`rounded-full border px-4 py-2 text-[14px] transition-colors ${id === e.id ? "border-[rgba(var(--tint),0.6)] bg-[rgba(var(--tint),0.1)] text-text" : "border-line-strong text-muted hover:text-text"}`}
              >
                {e.title}
              </button>
            ))}
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <AnimatePresence mode="wait" initial={false}>
              <motion.div key={ex.id + "-msg"} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.4, ease: EASE }} className="surface p-6 sm:p-7">
                <div className="mb-5 flex items-center justify-between">
                  <span className="label">{ex.kind} · illustrative</span>
                  <span className="inline-flex items-center gap-1.5 text-[12px] text-warn"><TriangleAlert size={13} /> Scam pattern</span>
                </div>
                <p className="rounded-xl border border-line-strong bg-ink/70 p-5 font-mono text-[13.5px] leading-[1.85] text-text/90">{ex.message}</p>
                <button type="button" onClick={() => onTry({ message: ex.message, org: ex.org })} className="btn-primary mt-6 w-full sm:w-auto">
                  Check it with ScamShield <ArrowRight size={16} />
                </button>
              </motion.div>
            </AnimatePresence>

            <div className="space-y-3">
              <p className="label">Why it is suspicious</p>
              {ex.flags.map(([what, why], i) => {
                const open = shown > i;
                return (
                  <button
                    key={ex.id + what} type="button" onClick={() => setShown(open ? i : i + 1)} aria-expanded={open}
                    className={`block w-full rounded-xl border p-4 text-left transition-colors duration-300 ${open ? "border-[rgba(255,176,32,0.4)] bg-[rgba(255,176,32,0.05)]" : "border-line-strong hover:border-[var(--line-hover)]"}`}
                  >
                    <span className="flex items-center gap-3">
                      <span className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[12px] font-semibold ${open ? "bg-warn text-ink" : "border border-line-strong text-faint"}`}>{i + 1}</span>
                      <span className="text-[15.5px] font-medium text-text">{what}</span>
                    </span>
                    <AnimatePresence initial={false}>
                      {open && (
                        <motion.span initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.4, ease: EASE }} className="block overflow-hidden">
                          <span className="block pl-9 pt-2.5 text-[14.5px] leading-relaxed text-muted">{why}</span>
                        </motion.span>
                      )}
                    </AnimatePresence>
                  </button>
                );
              })}
              <button type="button" onClick={() => setShown(ex.flags.length)} className="pt-1 text-[13px] text-muted underline decoration-line-strong underline-offset-4 transition-colors hover:text-text">Reveal all</button>
            </div>
          </div>
        </FadeUp>
      </div>
    </section>
  );
}
