import { motion } from "motion/react";
import { ArrowUpRight, Phone } from "lucide-react";
import { AFTER_A_SCAM, HELPLINE, RESOURCE_GROUPS } from "../../data/resources";
import { EASE, FadeUp, SectionHead } from "../ui/Reveal";

export function ExternalLink({ href, children, className = "" }) {
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" className={className}>
      {children}
      <span className="sr-only"> (opens in a new tab)</span>
    </a>
  );
}

export default function Help() {
  return (
    <section id="help" className="relative px-5 pb-24 pt-14 sm:px-8 sm:pb-32">
      <div className="mx-auto max-w-[1200px]">
        <SectionHead eyebrow="Need more help?" title="If something already went wrong, act fast.">
          A tool can only tell you what a message looks like. These official services can stop a scam, report it and help you recover.
        </SectionHead>

        {/* helpline band */}
        <FadeUp className="mt-12">
          <div className="relative overflow-hidden rounded-2xl border border-[rgba(var(--tint),0.28)] bg-[linear-gradient(120deg,rgba(var(--tint),0.1),rgba(var(--tint),0.02)_55%)] p-7 sm:p-10">
            <div aria-hidden className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full border border-[rgba(var(--tint),0.18)]" />
            <div aria-hidden className="pointer-events-none absolute -right-10 -top-10 h-44 w-44 rounded-full border border-[rgba(var(--tint),0.18)]" />
            <div className="relative flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="label !text-[rgb(var(--tint))]">{HELPLINE.label}</p>
                <p className="display mt-2 text-[clamp(4rem,10vw,6.5rem)] leading-[0.9]">{HELPLINE.number}</p>
                <p className="mt-3 max-w-[44ch] text-[15px] text-muted">{HELPLINE.note}</p>
              </div>
              <a href={`tel:${HELPLINE.number}`} className="btn-primary self-start sm:self-center"><Phone size={16} /> Call {HELPLINE.number}</a>
            </div>
          </div>
        </FadeUp>

        {/* steps after a scam */}
        <div className="mt-16">
          <FadeUp><p className="label mb-5">If you have already lost money or shared a code</p></FadeUp>
          <ol className="grid gap-px overflow-hidden rounded-xl border border-line bg-line sm:grid-cols-2 lg:grid-cols-4">
            {AFTER_A_SCAM.map((s, i) => (
              <motion.li key={s.n} className="bg-ink p-6" initial={{ opacity: 0, y: 18 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: "-60px" }} transition={{ duration: 0.8, delay: i * 0.08, ease: EASE }}>
                <span className="display tint-text text-[2.6rem] leading-none">{s.n}</span>
                <h3 className="mt-3 text-[17px] font-medium">{s.title}</h3>
                <p className="mt-1.5 text-[14.5px] leading-relaxed text-muted">{s.text}</p>
              </motion.li>
            ))}
          </ol>
        </div>

        {/* resource library */}
        <div className="mt-20 grid gap-12 lg:grid-cols-3 lg:gap-10">
          {RESOURCE_GROUPS.map((g, gi) => (
            <FadeUp key={g.id} delay={gi * 0.1}>
              <h3 className="display text-[1.9rem]">{g.title}</h3>
              <p className="mt-1.5 text-[14.5px] text-muted">{g.blurb}</p>
              <ul className="mt-5 divide-y divide-line border-y border-line">
                {g.items.map((r) => (
                  <li key={r.href}>
                    <ExternalLink href={r.href} className="group block py-4">
                      <span className="flex items-start justify-between gap-3">
                        <span className="text-[15.5px] font-medium text-text transition-colors group-hover:tint-text">{r.title}</span>
                        <ArrowUpRight size={16} className="mt-1 shrink-0 text-faint transition-all duration-300 group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-[rgb(var(--tint))]" />
                      </span>
                      <span className="mt-1 block text-[13.5px] leading-relaxed text-muted">{r.note}</span>
                      <span className="mt-1.5 block font-mono text-[11px] text-faint">{r.org} · {new URL(r.href).hostname.replace(/^www\./, "")}</span>
                    </ExternalLink>
                  </li>
                ))}
              </ul>
            </FadeUp>
          ))}
        </div>
        <FadeUp className="mt-8 text-[13px] text-faint">Links go to the official sites and open in a new tab. ScamShield is not affiliated with any of them.</FadeUp>
      </div>
    </section>
  );
}
