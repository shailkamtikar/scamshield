import { motion, useReducedMotion, useScroll, useTransform } from "motion/react";
import { useRef } from "react";
import AnalyzeForm from "./AnalyzeForm";
import { EASE, FadeUp, SplitText } from "./ui/Reveal";

const SOURCES = ["Google Safe Browsing", "VirusTotal", "URLhaus", "OpenPhish", "urlscan.io sandbox"];

/** The lens: fine concentric rings behind the analyzer, drifting slowly and parallaxing on scroll. */
function Lens() {
  const reduce = useReducedMotion();
  const ref = useRef(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start start", "end start"] });
  const y = useTransform(scrollYProgress, [0, 1], [0, 140]);
  const scale = useTransform(scrollYProgress, [0, 1], [1, 1.18]);
  return (
    <motion.div ref={ref} aria-hidden className="pointer-events-none absolute inset-x-0 top-0 -z-10 h-[820px] overflow-hidden" style={{ y: reduce ? 0 : y }}>
      <motion.svg viewBox="0 0 1200 800" className="absolute left-1/2 top-[-60px] w-[1300px] max-w-none -translate-x-1/2" style={{ scale: reduce ? 1 : scale }} fill="none">
        <defs>
          <radialGradient id="lens-fade" cx="50%" cy="45%" r="55%">
            <stop offset="0%" stopColor="white" stopOpacity="1" />
            <stop offset="70%" stopColor="white" stopOpacity="0.35" />
            <stop offset="100%" stopColor="white" stopOpacity="0" />
          </radialGradient>
          <mask id="lens-mask"><rect width="1200" height="800" fill="url(#lens-fade)" /></mask>
        </defs>
        <g mask="url(#lens-mask)" stroke="rgb(var(--tint))" strokeOpacity="0.16">
          {[110, 190, 280, 380, 490, 610].map((r, i) => <circle key={r} cx="600" cy="360" r={r} strokeWidth={i === 2 ? 1.2 : 0.8} strokeDasharray={i % 2 ? "2 7" : undefined} />)}
          <line x1="0" y1="360" x2="1200" y2="360" strokeOpacity="0.07" /><line x1="600" y1="0" x2="600" y2="800" strokeOpacity="0.07" />
        </g>
        <g mask="url(#lens-mask)" style={{ transformOrigin: "600px 360px", animation: reduce ? undefined : "orbit 90s linear infinite" }}>
          <circle cx="600" cy="80" r="3.5" fill="rgb(var(--tint))" fillOpacity="0.8" />
          <circle cx="1090" cy="360" r="2.5" fill="rgb(var(--tint))" fillOpacity="0.5" />
          <circle cx="260" cy="620" r="2.5" fill="rgb(var(--tint))" fillOpacity="0.5" />
        </g>
      </motion.svg>
      <div className="absolute left-1/2 top-[120px] h-[520px] w-[820px] -translate-x-1/2 rounded-full bg-[radial-gradient(closest-side,rgba(var(--tint),0.13),transparent_72%)] transition-[background] duration-1000" />
    </motion.div>
  );
}

export default function Hero({ mode, onMode, onSubmit, prefill, engineDown }) {
  return (
    <section id="top" className="relative px-5 pb-12 pt-[128px] sm:px-8 sm:pt-[148px]">
      <Lens />
      <div className="mx-auto max-w-[1200px]">
        <div className="mx-auto max-w-[860px] text-center">
          <motion.span className="eyebrow justify-center" initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.05, ease: EASE }}>
            Scam &amp; phishing check
          </motion.span>
          <SplitText as="h1" now delay={0.1} className="display mt-5 text-[clamp(2.7rem,7.2vw,5.4rem)]">
            {["Don't trust the message.", { em: "Verify it.", accent: true }]}
          </SplitText>
          <motion.p className="mx-auto mt-6 max-w-[620px] text-[17px] leading-relaxed text-muted" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.9, delay: 0.45, ease: EASE }}>
            Suspicious messages, links, QR codes and emails can hide convincing scams. ScamShield helps you investigate them before you click.
          </motion.p>
        </div>

        <div className="mx-auto mt-10 max-w-[860px] sm:mt-12">
          <AnalyzeForm mode={mode} onMode={onMode} onSubmit={onSubmit} prefill={prefill} engineDown={engineDown} />
          <FadeUp delay={0.9} y={8} className="mt-6">
            <p className="flex flex-wrap items-center justify-center gap-x-5 gap-y-1.5 text-[12.5px] text-faint">
              <span>Links are checked with</span>
              {SOURCES.map((s, i) => (
                <span key={s} className="inline-flex items-center gap-5">
                  <span className="text-muted">{s}</span>{i < SOURCES.length - 1 && <span aria-hidden className="h-1 w-1 rounded-full bg-line-strong" />}
                </span>
              ))}
            </p>
          </FadeUp>
        </div>
      </div>
    </section>
  );
}
