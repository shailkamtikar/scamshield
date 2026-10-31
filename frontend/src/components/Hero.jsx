import { motion } from "motion/react";

const EASE = [0.16, 1, 0.3, 1];

function Line({ children, delay = 0, accent = false }) {
  return (
    <span className="block overflow-hidden pb-[0.06em]">
      <motion.span
        className={`display block ${accent ? "tint-text" : ""}`}
        initial={{ y: "105%" }}
        animate={{ y: 0 }}
        transition={{ duration: 1.1, delay, ease: EASE }}
      >
        {children}
      </motion.span>
    </span>
  );
}

export default function Hero() {
  return (
    <div className="pt-6 sm:pt-10">
      <motion.div
        className="label mb-5 flex items-center gap-3"
        initial={{ opacity: 0, x: -12 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.8, delay: 0.1, ease: EASE }}
      >
        <span className="inline-block h-px w-8 bg-[rgb(var(--tint))]" />
        Scam &amp; phishing intelligence
      </motion.div>
      <h1 className="text-[clamp(3.4rem,11.5vw,10.5rem)]">
        <Line delay={0.05}>Know before</Line>
        <Line delay={0.18} accent>you tap.</Line>
      </h1>
      <motion.p
        className="mt-6 max-w-[560px] text-[15px] leading-relaxed text-muted sm:text-[17px]"
        initial={{ opacity: 0, y: 14 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.9, delay: 0.55, ease: EASE }}
      >
        Paste a message, drop a screenshot or scan a QR code. ScamShield follows the link, checks it against live threat
        feeds, reads the wording, and tells you plainly whether it is safe to open.
      </motion.p>
    </div>
  );
}
