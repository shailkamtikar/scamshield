import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

export function Logo({ size = 28 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden className="shrink-0">
      <rect width="32" height="32" rx="8" fill="var(--brand)" />
      <path d="M16 6.5 8.5 9.8v5.6c0 4.7 3.2 8 7.5 9.8 4.3-1.8 7.5-5.1 7.5-9.8V9.8L16 6.5Z" fill="none" stroke="var(--on-brand)" strokeWidth="2" />
      <path d="m12.5 15.8 2.5 2.5 4.5-4.6" fill="none" stroke="var(--on-brand)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ThemeToggle() {
  const [dark, setDark] = useState(() => document.documentElement.dataset.theme === "dark");
  useEffect(() => {
    if (dark) document.documentElement.dataset.theme = "dark";
    else delete document.documentElement.dataset.theme;
    try {
      localStorage.setItem("ss-theme", dark ? "dark" : "light");
    } catch {
      /* the choice just won't be remembered */
    }
  }, [dark]);
  return (
    <button type="button" onClick={() => setDark((d) => !d)} aria-label={dark ? "Switch to light mode" : "Switch to dark mode"} className="flex h-9 w-9 items-center justify-center rounded-full text-soft transition-colors hover:bg-sunken">
      {dark ? <Sun size={18} /> : <Moon size={18} />}
    </button>
  );
}

export function Header({ health, onHome }) {
  const offline = health === null;
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-page/85 backdrop-blur-md">
      <div className="mx-auto flex h-[60px] max-w-[880px] items-center justify-between px-4 sm:px-6">
        <button type="button" onClick={onHome} className="flex items-center gap-2.5" aria-label="ScamShield home">
          <Logo />
          <span className="font-serif text-[19px] font-semibold tracking-tight">ScamShield</span>
        </button>
        <div className="flex items-center gap-2">
          {offline && <span className="rounded-full bg-sunken px-3 py-1 text-[13px] text-soft">Service unavailable</span>}
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}

export function Footer() {
  return (
    <footer className="mt-10 border-t border-line">
      <div className="mx-auto max-w-[880px] space-y-2 px-4 py-8 text-[14px] leading-relaxed text-soft sm:px-6">
        <p>
          <b className="font-semibold text-ink">Lost money or shared an OTP?</b> Call the national cyber helpline <b className="font-semibold text-ink">1930</b> straight away, or report at cybercrime.gov.in.
        </p>
        <p>
          ScamShield gives an automated opinion, not a guarantee. We don't keep what you check, but to analyse it we send the text to Google Gemini and the links to security services such as Google Safe Browsing and VirusTotal, so please don't paste passwords or OTPs.
        </p>
      </div>
    </footer>
  );
}
