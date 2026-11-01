import { AnimatePresence, motion } from "motion/react";
import { X } from "lucide-react";
import { useEffect, useState } from "react";
import { Logo } from "./Nav";
import { ExternalLink } from "./sections/Help";

const REPO = "https://github.com/shailkamtikar/scamshield";

function TermsDialog({ open, onClose }) {
  useEffect(() => {
    if (!open) return undefined;
    const esc = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [open, onClose]);
  return (
    <AnimatePresence>
      {open && (
        <motion.div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose}>
          <motion.div role="dialog" aria-modal="true" aria-label="Terms of use" className="surface max-h-[85vh] w-full max-w-[560px] overflow-y-auto p-7" initial={{ y: 24, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ y: 12, opacity: 0 }} transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }} onClick={(e) => e.stopPropagation()}>
            <div className="mb-4 flex items-start justify-between">
              <h2 className="display text-[2rem]">Terms of use</h2>
              <button type="button" onClick={onClose} aria-label="Close" className="rounded-lg p-1.5 text-muted hover:text-text"><X size={18} /></button>
            </div>
            <ul className="space-y-3 text-[14.5px] leading-relaxed text-muted">
              <li>ScamShield gives an automated assessment from the information available at the moment you check. It is not a guarantee that something is safe or unsafe.</li>
              <li>Do not rely on it as the only basis for a decision about money or personal data. Confirm through the organisation's official app, website or helpline.</li>
              <li>Do not submit passwords, PINs or OTPs, and do not submit content you have no right to share.</li>
              <li>The service is free and provided as it is, with no warranty. It may be unavailable, and its results may be wrong.</li>
              <li>If you have lost money, call 1930 and report at cybercrime.gov.in straight away.</li>
            </ul>
            <p className="mt-5 text-[12.5px] text-faint">This is a plain-language summary for a student-built project, not a legal agreement drafted by a lawyer.</p>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function Col({ title, children }) {
  return (
    <div>
      <h3 className="label mb-4">{title}</h3>
      <ul className="space-y-2.5 text-[14.5px]">{children}</ul>
    </div>
  );
}
const linkCls = "text-muted transition-colors hover:text-text";

export default function Footer({ onGo, onCheck }) {
  const [terms, setTerms] = useState(false);
  return (
    <footer className="relative px-5 pb-10 pt-20 sm:px-8">
      <div className="mx-auto max-w-[1200px]">
        <div className="grid gap-12 lg:grid-cols-[1.5fr_1fr_1fr_1fr]">
          <div>
            <Logo onClick={() => onGo("top")} />
            <p className="mt-4 max-w-[34ch] text-[14.5px] leading-relaxed text-muted">Investigate suspicious messages, links, QR codes and emails before you click. Built for Indian users.</p>
          </div>
          <Col title="Product">
            <li><button type="button" onClick={onCheck} className={linkCls}>Message scanner</button></li>
            <li><button type="button" onClick={() => onGo("how")} className={linkCls}>How it works</button></li>
            <li><button type="button" onClick={() => onGo("library")} className={linkCls}>Threat library</button></li>
            <li><ExternalLink href="https://t.me/ScamshieldAPIbot" className={linkCls}>Check on Telegram</ExternalLink></li>
          </Col>
          <Col title="Resources">
            <li><button type="button" onClick={() => onGo("signs")} className={linkCls}>Scam awareness</button></li>
            <li><button type="button" onClick={() => onGo("tips")} className={linkCls}>Safety tips (works offline)</button></li>
            <li><button type="button" onClick={() => onGo("help")} className={linkCls}>Cybersecurity resources</button></li>
            <li><ExternalLink href="https://cybercrime.gov.in" className={linkCls}>Report cybercrime</ExternalLink></li>
          </Col>
          <Col title="Company">
            <li><button type="button" onClick={() => onGo("privacy")} className={linkCls}>About</button></li>
            <li><ExternalLink href={REPO} className={linkCls}>Contact (GitHub)</ExternalLink></li>
            <li><button type="button" onClick={() => onGo("privacy")} className={linkCls}>Privacy policy</button></li>
            <li><button type="button" onClick={() => setTerms(true)} className={linkCls}>Terms of service</button></li>
          </Col>
        </div>
        <div className="mt-14 flex flex-col gap-3 border-t border-line pt-6 text-[12.5px] text-faint sm:flex-row sm:justify-between">
          <span>ScamShield is an automated assessment, not a guarantee. If you lost money, call <b className="font-medium text-muted">1930</b> or report at cybercrime.gov.in.</span>
          <span>© {new Date().getFullYear()} ScamShield</span>
        </div>
      </div>
      <TermsDialog open={terms} onClose={() => setTerms(false)} />
    </footer>
  );
}
