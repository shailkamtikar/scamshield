import { AnimatePresence, motion } from "motion/react";
import { Plus } from "lucide-react";
import { useState } from "react";
import { SIGNS, SIGN_MESSAGE } from "../../data/scams";
import { EASE, FadeUp, SectionHead } from "../ui/Reveal";

export default function WarningSigns() {
  const [sel, setSel] = useState("urgent");

  return (
    <section id="signs" className="relative px-5 py-24 sm:px-8 sm:py-32">
      <div className="mx-auto grid max-w-[1200px] gap-14 lg:grid-cols-[minmax(0,6fr)_minmax(0,5fr)] lg:gap-20">
        <div className="lg:order-2 lg:sticky lg:top-28 lg:self-start">
          <FadeUp>
            <div className="surface p-5 sm:p-7">
              <div className="mb-5 flex items-center justify-between">
                <span className="label">Illustrative message</span>
                <span className="text-[12px] text-faint">Hover or tap a sign to light it up</span>
              </div>
              <p className="rounded-xl border border-line-strong bg-ink/70 p-5 text-[16px] leading-[1.9] text-muted">
                {SIGN_MESSAGE.map((p, i) =>
                  p.s ? (
                    <button
                      key={i} type="button" onClick={() => setSel(p.s)} aria-label={`Warning sign: ${SIGNS.find((s) => s.id === p.s).title}`}
                      className={`rounded-[5px] px-1 py-0.5 text-left transition-all duration-500 ${sel === p.s ? "bg-[rgba(255,176,32,0.18)] text-warn shadow-[0_0_0_1px_rgba(255,176,32,0.45)]" : "text-text/90 underline decoration-line-strong decoration-dotted underline-offset-4 hover:text-warn"}`}
                    >
                      {p.t}
                    </button>
                  ) : (
                    <span key={i}>{p.t}</span>
                  ),
                )}
              </p>
              <AnimatePresence mode="wait" initial={false}>
                <motion.p key={sel} className="mt-4 text-[14px] text-muted" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.35 }}>
                  <span className="text-warn">What to do: </span>{SIGNS.find((s) => s.id === sel).tip}
                </motion.p>
              </AnimatePresence>
            </div>
          </FadeUp>
        </div>

        <div className="lg:order-1">
          <SectionHead eyebrow="Understand the warning signs" title="The small things that give a scam away.">
            Learn to spot these six and you will catch most scams before any tool has to.
          </SectionHead>
          <FadeUp delay={0.1}>
            <ul className="mt-10 divide-y divide-line border-y border-line">
              {SIGNS.map((s, i) => {
                const on = sel === s.id;
                return (
                  <li key={s.id}>
                    <button type="button" aria-expanded={on} onClick={() => setSel(s.id)} onMouseEnter={() => matchMedia("(hover: hover)").matches && setSel(s.id)} className="group flex w-full items-start gap-4 py-5 text-left">
                      <span className={`mt-1 font-mono text-[11.5px] ${on ? "text-warn" : "text-faint"}`}>{String(i + 1).padStart(2, "0")}</span>
                      <span className="min-w-0 flex-1">
                        <span className={`block text-[17.5px] font-medium transition-colors ${on ? "text-text" : "text-muted group-hover:text-text"}`}>{s.title}</span>
                        <AnimatePresence initial={false}>
                          {on && (
                            <motion.span initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.45, ease: EASE }} className="block overflow-hidden">
                              <span className="block pt-2 text-[15px] leading-relaxed text-muted">{s.text}</span>
                            </motion.span>
                          )}
                        </AnimatePresence>
                      </span>
                      <Plus size={18} className={`mt-1 shrink-0 text-faint transition-transform duration-300 ${on ? "rotate-45 text-warn" : ""}`} />
                    </button>
                  </li>
                );
              })}
            </ul>
          </FadeUp>
        </div>
      </div>
    </section>
  );
}
