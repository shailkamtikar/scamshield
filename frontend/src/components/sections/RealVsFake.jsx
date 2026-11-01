import { AnimatePresence, motion } from "motion/react";
import { Check, Eye, X } from "lucide-react";
import { useState } from "react";
import DiffAddress from "../DiffAddress";
import { EASE, FadeUp, SectionHead } from "../ui/Reveal";

/** Illustrative address pairs. The real ones are the organisations' genuine addresses; the fake ones are made up for teaching. */
const PAIRS = [
  { id: "sbi", label: "A name inside someone else's address", real: "sbi.co.in", fake: "sbi-kyc-update.top", owner: "sbi-kyc-update.top", note: "The bank's name is only part of a longer name that belongs to someone else. The bit before .top is what counts." },
  { id: "sub", label: "The real name as a decoy in front", real: "hdfcbank.com", fake: "hdfcbank.com.secure-login.info", owner: "secure-login.info", note: "Read an address from the right. The owner is the last name before the ending (here secure-login.info). Everything in front is decoration." },
  { id: "rn", label: "Letters that look alike", real: "amazon.in", fake: "arnazon.in", owner: "arnazon.in", note: "\"rn\" looks like \"m\" at a glance, especially on a phone. Zoom in or type the address yourself." },
  { id: "extra", label: "One extra letter", real: "google.com", fake: "gooogle.com", owner: "gooogle.com", note: "A single added letter is enough to be a different, scammer-owned address." },
  { id: "gov", label: "A dash instead of a dot", real: "incometax.gov.in", fake: "incometax-gov.in", owner: "incometax-gov.in", note: "Real government sites end in .gov.in, a zone only the government can register. A dash is just an ordinary name anyone can buy." },
];

export default function RealVsFake() {
  const [id, setId] = useState(PAIRS[0].id);
  const [reveal, setReveal] = useState(false);
  const pair = PAIRS.find((p) => p.id === id);
  return (
    <section id="compare" className="relative border-t border-line px-5 py-24 sm:px-8 sm:py-32">
      <div className="mx-auto max-w-[1200px]">
        <SectionHead eyebrow="Real vs fake" title="Spot the address that only looks right.">
          Most scam links are one clever address away from the real thing. Compare each pair, then reveal what gives the fake away.
        </SectionHead>

        <FadeUp delay={0.1} className="mt-12">
          <div role="tablist" aria-label="Address pairs" className="mb-6 flex flex-wrap gap-2">
            {PAIRS.map((p) => (
              <button key={p.id} type="button" role="tab" aria-selected={id === p.id} onClick={() => { setId(p.id); setReveal(false); }}
                className={`rounded-full border px-4 py-2 text-[14px] transition-colors ${id === p.id ? "border-[rgba(var(--tint),0.6)] bg-[rgba(var(--tint),0.1)] text-text" : "border-line-strong text-muted hover:text-text"}`}>
                {p.label}
              </button>
            ))}
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <div className="surface p-6 sm:p-8">
              <p className="mb-4 flex items-center gap-2 text-[13px] font-medium text-safe"><Check size={16} /> The real address</p>
              <p className="break-all font-mono text-[clamp(1rem,2.4vw,1.5rem)] leading-snug text-text">{pair.real}</p>
              <p className="mt-4 text-[13px] text-faint">Illustrative pair. Always type the address yourself or use the official app.</p>
            </div>
            <div className="surface p-6 sm:p-8">
              <p className="mb-4 flex items-center gap-2 text-[13px] font-medium text-danger"><X size={16} /> The fake address</p>
              <DiffAddress real={pair.real} fake={pair.fake} owner={pair.owner} reveal={reveal} />
              <div className="mt-4 min-h-[3.5rem]">
                <AnimatePresence mode="wait" initial={false}>
                  {reveal ? (
                    <motion.p key="note" initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: 0.4, ease: EASE }} className="text-[14.5px] leading-relaxed text-muted">
                      <b className="font-medium text-text">Owner: {pair.owner}.</b> {pair.note}
                    </motion.p>
                  ) : (
                    <motion.button key="btn" type="button" onClick={() => setReveal(true)} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="btn-ghost !py-2 !text-[13.5px]">
                      <Eye size={15} /> Show what is different
                    </motion.button>
                  )}
                </AnimatePresence>
              </div>
            </div>
          </div>
        </FadeUp>
      </div>
    </section>
  );
}
