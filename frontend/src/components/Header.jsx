import ThemeToggle from "./ThemeToggle";

export default function Header({ backendOnline }) {
  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-border bg-bg/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-[860px] items-center justify-between gap-4 px-4 md:px-8">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-accent-fg">
            <span className="material-symbols-outlined text-[20px]" style={{ fontVariationSettings: "'FILL' 1" }}>
              shield
            </span>
          </div>
          <span className="font-display text-[1.125rem] font-semibold tracking-tight text-text">
            ScamShield
          </span>
          <span className="rounded bg-surface-high px-1.5 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-text-muted">
            v1.0
          </span>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden items-center gap-1.5 rounded-full bg-surface-high px-2.5 py-1 sm:flex">
            <span className="relative flex h-2 w-2">
              {backendOnline && (
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-positive opacity-75" />
              )}
              <span
                className={`relative inline-flex h-2 w-2 rounded-full ${
                  backendOnline ? "bg-positive" : "bg-risk-critical"
                }`}
              />
            </span>
            <span className="font-mono text-[11px] text-text-muted">
              {backendOnline === null
                ? "Checking engine…"
                : backendOnline
                ? "Engine Online"
                : "Engine Unreachable"}
            </span>
          </div>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
