import { motion, useReducedMotion } from "motion/react";
import { Check, FileText, Link2, QrCode, ScanLine } from "lucide-react";
import { EASE, FadeUp, SectionHead } from "../ui/Reveal";

const inView = { once: true, margin: "-120px" };

function SubmitVisual() {
  const chips = [[FileText, "Message"], [Link2, "Link"], [ScanLine, "Screenshot"], [QrCode, "QR code"]];
  return (
    <div className="surface-flat p-5">
      <div className="rounded-lg border border-line-strong bg-ink/70 p-4">
        <p className="font-mono text-[13px] leading-relaxed text-muted">
          <motion.span initial={{ width: 0 }} whileInView={{ width: "100%" }} viewport={inView} transition={{ duration: 2.2, ease: "linear" }} className="inline-block max-w-full overflow-hidden whitespace-nowrap align-bottom">
            Your parcel is held. Pay Rs 25 at dc9x35ez.top
          </motion.span>
          <motion.span className="ml-0.5 inline-block h-[15px] w-[7px] translate-y-[2px] bg-[rgb(var(--tint))]" animate={{ opacity: [1, 0, 1] }} transition={{ duration: 1, repeat: Infinity }} />
        </p>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {chips.map(([Icon, label], i) => (
          <motion.span key={label} initial={{ opacity: 0, scale: 0.9, y: 8 }} whileInView={{ opacity: 1, scale: 1, y: 0 }} viewport={inView} transition={{ delay: 0.3 + i * 0.12, duration: 0.6, ease: EASE }} className="inline-flex items-center gap-1.5 rounded-full border border-line-strong px-3 py-1.5 text-[12.5px] text-muted">
            <Icon size={13} className="tint-text" /> {label}
          </motion.span>
        ))}
      </div>
    </div>
  );
}

const CHECKS = ["Follows every redirect", "Compares threat lists", "Reads the domain's age", "Inspects the page as text", "Opens it in a sandbox if needed"];

function InvestigateVisual() {
  const reduce = useReducedMotion();
  return (
    <div className="surface-flat relative overflow-hidden p-5">
      <p className="mb-4 truncate font-mono text-[12.5px] text-faint">https://dc9x35ez.top/pay</p>
      <ul className="space-y-2.5">
        {CHECKS.map((c, i) => (
          <motion.li key={c} className="flex items-center gap-3 text-[14px]" initial={reduce ? false : { opacity: 0.35 }} whileInView={{ opacity: 1 }} viewport={inView} transition={{ delay: 0.25 + i * 0.35, duration: 0.5 }}>
            <motion.span className="flex h-5 w-5 items-center justify-center rounded-full bg-[rgb(var(--tint))] text-ink" initial={reduce ? false : { scale: 0 }} whileInView={{ scale: 1 }} viewport={inView} transition={{ delay: 0.45 + i * 0.35, type: "spring", stiffness: 500, damping: 20 }}>
              <Check size={12} strokeWidth={3} />
            </motion.span>
            <span className="text-muted">{c}</span>
          </motion.li>
        ))}
      </ul>
      {!reduce && <div className="scanline pointer-events-none absolute inset-x-0 top-0 h-14" style={{ animation: "scan-sweep 4.5s ease-in-out infinite" }} />}
    </div>
  );
}

function UnderstandVisual() {
  const reasons = ["The link is a random name on a .top domain", "A fee for a parcel you didn't order", "Government posts don't ask for card details"];
  return (
    <div className="surface-flat p-5">
      <div className="flex items-end justify-between">
        <div>
          <p className="label">Assessment</p>
          <p className="display mt-1 text-[2.6rem] text-danger">Dangerous</p>
        </div>
        <p className="text-right text-[12.5px] text-faint">Example<br />illustration</p>
      </div>
      <div className="mt-4 h-1.5 overflow-hidden rounded-full bg-ink-3">
        <motion.div className="h-full rounded-full bg-gradient-to-r from-safe via-warn to-danger" initial={{ width: 0 }} whileInView={{ width: "86%" }} viewport={inView} transition={{ duration: 1.6, delay: 0.3, ease: EASE }} />
      </div>
      <ul className="mt-5 space-y-2.5">
        {reasons.map((r, i) => (
          <motion.li key={r} className="flex gap-2.5 text-[13.5px] text-muted" initial={{ opacity: 0, x: -10 }} whileInView={{ opacity: 1, x: 0 }} viewport={inView} transition={{ delay: 0.6 + i * 0.2, duration: 0.6, ease: EASE }}>
            <span className="mt-[8px] h-1.5 w-1.5 shrink-0 rounded-full bg-danger" />{r}
          </motion.li>
        ))}
      </ul>
    </div>
  );
}

const STEPS = [
  { n: "01", title: "Submit", text: "Paste a message, upload a screenshot, or provide a suspicious link. A QR code can be scanned with your camera: it is read on your device and never opened.", Visual: SubmitVisual },
  { n: "02", title: "Investigate", text: "ScamShield follows the link safely, checks it against threat lists and domain records, reads the wording, and inspects unfamiliar pages in an isolated browser, never on your device.", Visual: InvestigateVisual },
  { n: "03", title: "Understand", text: "You get a plain-language assessment with the reasons behind it, the warning signs found, and what to do next. The technical trail is there if you want it.", Visual: UnderstandVisual },
];

export default function HowItWorks() {
  return (
    <section id="how" className="relative px-5 pb-24 pt-14 sm:px-8 sm:pb-32">
      <div className="mx-auto grid max-w-[1200px] gap-14 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:gap-20">
        <div className="lg:sticky lg:top-32 lg:self-start">
          <SectionHead eyebrow="How it works" title="From a doubtful message to a clear answer.">
            Three steps, a few seconds, and nothing to install.
          </SectionHead>
        </div>
        <ol className="space-y-14 sm:space-y-20">
          {STEPS.map(({ n, title, text, Visual }) => (
            <li key={n}>
              <FadeUp>
                <div className="mb-4 flex items-baseline gap-4">
                  <span className="display tint-text text-[2.4rem] leading-none">{n}</span>
                  <h3 className="display text-[2rem]">{title}</h3>
                </div>
                <p className="mb-6 max-w-[52ch] text-[16px] leading-relaxed text-muted">{text}</p>
              </FadeUp>
              <FadeUp delay={0.1}><Visual /></FadeUp>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
