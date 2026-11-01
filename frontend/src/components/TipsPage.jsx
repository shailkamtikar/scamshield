import { motion } from "motion/react";
import { Check, Phone, WifiOff } from "lucide-react";
import { useState } from "react";
import { AFTER_A_SCAM } from "../data/resources";
import { CHECKLIST, DONTS, DOS, GLOSSARY, NUMBERS, RULES } from "../data/tips";
import { EASE, FadeUp, SectionHead } from "./ui/Reveal";

function Checklist() {
  const [done, setDone] = useState(() => new Set());
  const toggle = (i) => setDone((s) => { const n = new Set(s); if (n.has(i)) n.delete(i); else n.add(i); return n; });
  return (
    <div className="surface p-5 sm:p-7">
      <ul className="space-y-1">
        {CHECKLIST.map((q, i) => {
          const on = done.has(i);
          return (
            <li key={q}>
              <button type="button" onClick={() => toggle(i)} aria-pressed={on} className="flex w-full items-start gap-3.5 rounded-lg px-2 py-3 text-left transition-colors hover:bg-[var(--ghost)]">
                <span className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-md border transition-colors ${on ? "border-transparent bg-[rgb(var(--tint))] text-[var(--on-tint)]" : "border-line-strong"}`}>{on && <Check size={13} strokeWidth={3} />}</span>
                <span className={`text-[15.5px] leading-relaxed transition-colors ${on ? "text-faint line-through" : "text-text"}`}>{q}</span>
              </button>
            </li>
          );
        })}
      </ul>
      <p className="mt-3 px-2 text-[13px] text-faint">If any answer worries you, stop and check through the official app or number. Tap a line to tick it off.</p>
    </div>
  );
}

export default function TipsPage({ onCheck }) {
  return (
    <div className="mx-auto max-w-[1000px] px-5 pb-24 pt-[120px] sm:px-8 sm:pt-[140px]">
      <SectionHead eyebrow="Safety tips" title="Stay safe, even when you are offline.">
        Everything on this page is stored on your device after your first visit, so you can read it without a connection.
      </SectionHead>
      <FadeUp delay={0.2} className="mt-5">
        <span className="inline-flex items-center gap-2 rounded-full border border-line-strong px-3.5 py-1.5 text-[12.5px] text-muted"><WifiOff size={14} className="tint-text" /> Works without internet</span>
      </FadeUp>

      <section className="mt-16">
        <h2 className="display text-[2rem]">Six rules that stop most scams</h2>
        <ol className="mt-6 grid gap-px overflow-hidden rounded-xl border border-line bg-line sm:grid-cols-2">
          {RULES.map((r, i) => (
            <motion.li key={r.n} className="bg-ink p-6" initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-40px" }} transition={{ duration: 0.7, delay: (i % 2) * 0.08, ease: EASE }}>
              <span className="display tint-text text-[2.2rem] leading-none">{r.n}</span>
              <h3 className="mt-2 text-[16.5px] font-medium">{r.title}</h3>
              <p className="mt-1.5 text-[14.5px] leading-relaxed text-muted">{r.text}</p>
            </motion.li>
          ))}
        </ol>
      </section>

      <section className="mt-16">
        <h2 className="display text-[2rem]">Before you tap, ask yourself</h2>
        <FadeUp className="mt-6"><Checklist /></FadeUp>
      </section>

      <section className="mt-16 grid gap-8 sm:grid-cols-2">
        <FadeUp>
          <h2 className="display text-[2rem]">Do</h2>
          <ul className="mt-5 space-y-3">{DOS.map((d) => <li key={d} className="flex gap-3 text-[15px] leading-relaxed text-muted"><Check size={16} className="mt-[5px] shrink-0 text-safe" />{d}</li>)}</ul>
        </FadeUp>
        <FadeUp delay={0.1}>
          <h2 className="display text-[2rem]">Don't</h2>
          <ul className="mt-5 space-y-3">{DONTS.map((d) => <li key={d} className="flex gap-3 text-[15px] leading-relaxed text-muted"><span className="mt-[5px] shrink-0 font-semibold text-danger" aria-hidden>×</span>{d}</li>)}</ul>
        </FadeUp>
      </section>

      <section className="mt-16">
        <h2 className="display text-[2rem]">Scam words, in plain language</h2>
        <FadeUp className="mt-6">
          <dl className="divide-y divide-line border-y border-line">
            {GLOSSARY.map(([k, v]) => (
              <div key={k} className="grid gap-1 py-4 sm:grid-cols-[220px_1fr] sm:gap-6">
                <dt className="text-[15.5px] font-medium">{k}</dt>
                <dd className="text-[14.5px] leading-relaxed text-muted">{v}</dd>
              </div>
            ))}
          </dl>
        </FadeUp>
      </section>

      <section className="mt-16">
        <h2 className="display text-[2rem]">If it already happened</h2>
        <ol className="mt-6 grid gap-px overflow-hidden rounded-xl border border-line bg-line sm:grid-cols-2 lg:grid-cols-4">
          {AFTER_A_SCAM.map((s) => (
            <li key={s.n} className="bg-ink p-5">
              <span className="display tint-text text-[2rem] leading-none">{s.n}</span>
              <h3 className="mt-2 text-[16px] font-medium">{s.title}</h3>
              <p className="mt-1 text-[14px] leading-relaxed text-muted">{s.text}</p>
            </li>
          ))}
        </ol>
        <div className="mt-6 rounded-xl border border-[rgba(var(--tint),0.3)] bg-[rgba(var(--tint),0.06)] p-5">
          <p className="label mb-3 !text-[rgb(var(--tint))]">Numbers to keep</p>
          <ul className="space-y-2.5">{NUMBERS.map(([k, v]) => <li key={k} className="flex flex-col gap-0.5 sm:flex-row sm:gap-4"><b className="min-w-[150px] font-medium">{k}</b><span className="text-[14.5px] text-muted">{v}</span></li>)}</ul>
          <a href="tel:1930" className="btn-primary mt-5 !py-2.5 !text-[13.5px]"><Phone size={15} /> Call 1930</a>
        </div>
      </section>

      <div className="mt-16 border-t border-line pt-8">
        <p className="text-[15px] text-muted">Got a message you are not sure about?</p>
        <button type="button" onClick={onCheck} className="btn-primary mt-4">Check a message</button>
      </div>
    </div>
  );
}
