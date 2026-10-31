import { motion, useReducedMotion } from "motion/react";

export const EASE = [0.16, 1, 0.3, 1];

/** Fade and rise when scrolled into view. `delay` staggers siblings. */
export function FadeUp({ children, delay = 0, y = 24, className = "", as = "div", margin = "-80px" }) {
  const reduce = useReducedMotion();
  const Tag = motion[as] || motion.div;
  return (
    <Tag
      className={className}
      initial={reduce ? false : { opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin }}
      transition={{ duration: 0.9, delay, ease: EASE }}
    >
      {children}
    </Tag>
  );
}

/**
 * Headline that reveals word by word (each word rises out of a clipped line).
 * `now` plays on mount; otherwise it plays when the heading scrolls into view.
 * Wrap a word in {em: "word"} to italicise it.
 */
export function SplitText({ children, className = "", delay = 0, now = false, as: Tag = "h2", stagger = 0.045 }) {
  const reduce = useReducedMotion();
  const parts = Array.isArray(children) ? children : [children];
  const words = parts.flatMap((p, pi) =>
    typeof p === "string"
      ? p.split(" ").filter(Boolean).map((w, i) => ({ w, key: `${pi}-${i}` }))
      : [{ w: p.em, em: true, key: `${pi}-em`, accent: p.accent }],
  );
  const trigger = now ? { animate: "show" } : { whileInView: "show", viewport: { once: true, margin: "-80px" } };
  return (
    <Tag className={className} aria-label={words.map((x) => x.w).join(" ")}>
      <motion.span
        aria-hidden
        className="inline"
        initial={reduce ? "show" : "hide"}
        {...trigger}
        variants={{ show: { transition: { staggerChildren: stagger, delayChildren: delay } }, hide: {} }}
      >
        {words.map((x) => (
          <span key={x.key} className="inline-block overflow-hidden pb-[0.12em] align-bottom">
            <motion.span
              className={`inline-block ${x.em ? "italic" : ""} ${x.accent ? "tint-text" : ""}`}
              variants={{ hide: { y: "110%" }, show: { y: 0, transition: { duration: 1, ease: EASE } } }}
            >
              {x.w}&nbsp;
            </motion.span>
          </span>
        ))}
      </motion.span>
    </Tag>
  );
}

export function SectionHead({ eyebrow, title, children, className = "" }) {
  return (
    <div className={className}>
      {eyebrow && <FadeUp y={10}><span className="eyebrow">{eyebrow}</span></FadeUp>}
      <SplitText className="display mt-4 max-w-[18ch] text-[clamp(2.2rem,5vw,3.8rem)]">{title}</SplitText>
      {children && <FadeUp delay={0.15} className="mt-5 max-w-[56ch] text-[16.5px] leading-relaxed text-muted">{children}</FadeUp>}
    </div>
  );
}

/** A hairline that draws itself and ends in a small ring: links one section to the next. */
export function Connector() {
  const reduce = useReducedMotion();
  return (
    <div aria-hidden className="flex flex-col items-center">
      <motion.span className="block h-24 w-px origin-top bg-gradient-to-b from-transparent via-[rgba(var(--tint),0.5)] to-[rgba(var(--tint),0.8)]" initial={reduce ? false : { scaleY: 0 }} whileInView={{ scaleY: 1 }} viewport={{ once: true, margin: "-40px" }} transition={{ duration: 1.2, ease: EASE }} />
      <motion.span className="block h-2.5 w-2.5 rounded-full border border-[rgb(var(--tint))] bg-ink" initial={reduce ? false : { scale: 0 }} whileInView={{ scale: 1 }} viewport={{ once: true }} transition={{ delay: 0.9, type: "spring", stiffness: 400, damping: 18 }} />
    </div>
  );
}
