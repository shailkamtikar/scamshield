import { AnimatePresence, motion, useScroll, useSpring } from "motion/react";
import { ArrowRight, Menu, X } from "lucide-react";
import { useEffect, useState } from "react";

export const NAV = [
  { id: "top", label: "Home" },
  { id: "how", label: "How it works" },
  { id: "library", label: "Threat library" },
  { id: "help", label: "Resources" },
  { id: "privacy", label: "About" },
];

export function Logo({ onClick, size = 24 }) {
  return (
    <button type="button" onClick={onClick} className="group flex items-center gap-2.5" aria-label="ScamShield, back to top">
      <svg width={size} height={size} viewBox="0 0 24 24" fill="none" aria-hidden className="transition-transform duration-500 group-hover:rotate-[-8deg]">
        <path d="M12 2.2 4.2 5.6v5.9c0 4.8 3.3 8.4 7.8 10.3 4.5-1.9 7.8-5.5 7.8-10.3V5.6L12 2.2Z" stroke="rgb(var(--tint))" strokeWidth="1.5" strokeLinejoin="round" />
        <circle cx="12" cy="11.6" r="3.1" stroke="rgb(var(--tint))" strokeWidth="1.5" />
        <path d="m14.4 14 2.2 2.2" stroke="rgb(var(--tint))" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
      <span className="display text-[25px] leading-none tracking-tight">Scam<em>Shield</em></span>
    </button>
  );
}

function useActiveSection(ids) {
  const [active, setActive] = useState(ids[0]);
  useEffect(() => {
    const els = ids.map((id) => document.getElementById(id)).filter(Boolean);
    if (!els.length) return undefined;
    const io = new IntersectionObserver(
      (entries) => {
        const visible = entries.filter((e) => e.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (visible) setActive(visible.target.id);
      },
      { rootMargin: "-35% 0px -55% 0px", threshold: [0, 0.2, 0.6, 1] },
    );
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, [ids]);
  return active;
}

export default function Nav({ onGo, onCheck, showSections }) {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const { scrollYProgress } = useScroll();
  const progress = useSpring(scrollYProgress, { stiffness: 120, damping: 28, restDelta: 0.001 });
  const active = useActiveSection(NAV.map((n) => n.id));

  useEffect(() => {
    const on = () => setScrolled(window.scrollY > 24);
    on();
    window.addEventListener("scroll", on, { passive: true });
    return () => window.removeEventListener("scroll", on);
  }, []);

  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    const esc = (e) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", esc);
    return () => { document.body.style.overflow = ""; window.removeEventListener("keydown", esc); };
  }, [open]);

  const go = (id) => { setOpen(false); onGo(id); };

  return (
    <>
      <header className={`fixed inset-x-0 top-0 z-[61] transition-[background,border-color,backdrop-filter] duration-500 ${scrolled || open ? "border-b border-line bg-ink/80 backdrop-blur-xl" : "border-b border-transparent"}`}>
        <div className="mx-auto flex h-[68px] max-w-[1200px] items-center justify-between px-5 sm:px-8">
          <Logo onClick={() => go("top")} />
          <nav aria-label="Main" className="hidden items-center gap-1 lg:flex">
            {NAV.map((n) => (
              <button key={n.id} type="button" onClick={() => go(n.id)} className={`group relative rounded-md px-3.5 py-2 text-[14px] transition-colors ${showSections && active === n.id ? "text-text" : "text-muted hover:text-text"}`}>
                {n.label}
                <span className={`absolute inset-x-3.5 -bottom-px h-px origin-left bg-[rgb(var(--tint))] transition-transform duration-500 ease-[var(--ease-out-expo)] ${showSections && active === n.id ? "scale-x-100" : "scale-x-0 group-hover:scale-x-100"}`} />
              </button>
            ))}
          </nav>
          <div className="flex items-center gap-2">
            <button type="button" onClick={() => { setOpen(false); onCheck(); }} className="btn-primary group hidden whitespace-nowrap !px-4 !py-2.5 !text-[13.5px] sm:inline-flex">
              Check a message <ArrowRight size={15} className="transition-transform group-hover:translate-x-0.5" />
            </button>
            <button type="button" onClick={() => setOpen((v) => !v)} aria-expanded={open} aria-label={open ? "Close menu" : "Open menu"} className="flex h-10 w-10 items-center justify-center rounded-lg border border-line-strong text-muted lg:hidden">
              {open ? <X size={18} /> : <Menu size={18} />}
            </button>
          </div>
        </div>
        <motion.div aria-hidden className="absolute inset-x-0 bottom-[-1px] h-px origin-left bg-[rgba(var(--tint),0.7)]" style={{ scaleX: progress, opacity: scrolled ? 1 : 0 }} />
      </header>

      <AnimatePresence>
        {open && (
          <motion.div
            className="fixed inset-0 z-[60] flex flex-col bg-ink/95 px-6 pb-10 pt-[88px] backdrop-blur-2xl lg:hidden"
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.3 }}
            role="dialog" aria-label="Menu"
          >
            <nav className="flex flex-col">
              {NAV.map((n, i) => (
                <motion.button
                  key={n.id} type="button" onClick={() => go(n.id)}
                  className="display border-b border-line py-4 text-left text-[2.2rem]"
                  initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.06 * i + 0.1, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                >
                  {n.label}
                </motion.button>
              ))}
            </nav>
            <button type="button" onClick={() => { setOpen(false); onCheck(); }} className="btn-primary mt-auto w-full">Check a message <ArrowRight size={16} /></button>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
