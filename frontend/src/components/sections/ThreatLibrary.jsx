import { AnimatePresence, motion } from "motion/react";
import { ArrowUpRight, Flag } from "lucide-react";
import { useState } from "react";
import { CATEGORIES } from "../../data/scams";
import { EASE, FadeUp, SectionHead } from "../ui/Reveal";

export default function ThreatLibrary({ onTry }) {
  const [sel, setSel] = useState(CATEGORIES[0].id);
  const cat = CATEGORIES.find((c) => c.id === sel);
  const idx = CATEGORIES.indexOf(cat);

  return (
    <section id="library" className="relative border-y border-line bg-ink-2/40 px-5 py-24 sm:px-8 sm:py-32">
      <div className="mx-auto max-w-[1200px]">
        <SectionHead eyebrow="Threat library" title="Nine ways scammers get to you.">
          Each of these is something ScamShield looks for. Pick one to see how it works and what gives it away.
        </SectionHead>

        <div className="mt-14 grid gap-8 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:gap-14">
          <FadeUp>
            <ul role="tablist" aria-label="Scam types" aria-orientation="vertical" className="divide-y divide-line border-y border-line">
              {CATEGORIES.map((c, i) => {
                const on = c.id === sel;
                return (
                  <li key={c.id}>
                    <button
                      type="button" role="tab" aria-selected={on} aria-controls="library-panel" onClick={() => setSel(c.id)} onMouseEnter={() => matchMedia("(hover: hover)").matches && setSel(c.id)}
                      className="group relative flex w-full items-center gap-4 py-4 pr-2 text-left"
                    >
                      <span className={`font-mono text-[11.5px] transition-colors ${on ? "tint-text" : "text-faint"}`}>{String(i + 1).padStart(2, "0")}</span>
                      <span className="min-w-0 flex-1">
                        <span className={`block text-[17px] font-medium transition-colors ${on ? "text-text" : "text-muted group-hover:text-text"}`}>{c.name}</span>
                        <span className={`block overflow-hidden text-[13.5px] text-faint transition-[max-height,opacity] duration-500 ${on ? "max-h-12 opacity-100" : "max-h-0 opacity-0"}`}>{c.short}</span>
                      </span>
                      <ArrowUpRight size={17} className={`shrink-0 transition-all duration-300 ${on ? "tint-text translate-x-0 opacity-100" : "-translate-x-1 text-faint opacity-0 group-hover:opacity-100"}`} />
                      {on && <motion.span layoutId="lib-bar" className="absolute inset-y-0 left-[-14px] hidden w-[2px] bg-[rgb(var(--tint))] lg:block" transition={{ type: "spring", stiffness: 420, damping: 36 }} />}
                    </button>
                  </li>
                );
              })}
            </ul>
          </FadeUp>

          <FadeUp delay={0.1} className="lg:sticky lg:top-28 lg:self-start">
            <div id="library-panel" role="tabpanel" className="surface relative overflow-hidden p-6 sm:p-8">
              <span aria-hidden className="display pointer-events-none absolute -right-2 -top-6 select-none text-[11rem] leading-none text-white/[0.025]">{String(idx + 1).padStart(2, "0")}</span>
              <AnimatePresence mode="wait" initial={false}>
                <motion.div key={cat.id} initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.45, ease: EASE }}>
                  <h3 className="display text-[2.2rem]">{cat.name}</h3>
                  <p className="mt-3 max-w-[58ch] text-[16px] leading-relaxed text-muted">{cat.detail}</p>

                  <div className="mt-6 rounded-xl border border-line-strong bg-ink/70 p-4">
                    <p className="label mb-2 !text-faint">Illustrative example, not a real threat</p>
                    <p className="font-mono text-[13px] leading-relaxed text-text/90">{cat.sample}</p>
                  </div>

                  <p className="label mb-3 mt-7">What gives it away</p>
                  <ul className="space-y-2.5">
                    {cat.flags.map((f, i) => (
                      <motion.li key={f} className="flex gap-3 text-[15px] text-muted" initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.12 + i * 0.08, duration: 0.5, ease: EASE }}>
                        <Flag size={15} className="mt-[5px] shrink-0 text-warn" /> {f}
                      </motion.li>
                    ))}
                  </ul>

                  <button type="button" onClick={() => onTry({ message: cat.sample, org: "" })} className="btn-ghost mt-8">
                    Run this example through ScamShield <ArrowUpRight size={15} />
                  </button>
                </motion.div>
              </AnimatePresence>
            </div>
          </FadeUp>
        </div>
      </div>
    </section>
  );
}
