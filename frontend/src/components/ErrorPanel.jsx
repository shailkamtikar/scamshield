export default function ErrorPanel({ message, onRetry }) {
  return (
    <section className="rounded-2xl border border-risk-critical-edge/40 bg-risk-critical-bg p-6 text-center shadow-[var(--shadow-card)] md:p-8">
      <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-surface text-risk-critical">
        <span className="material-symbols-outlined text-[26px]">error</span>
      </div>
      <h2 className="font-display text-[1.25rem] font-semibold text-text">Something went wrong</h2>
      <p className="mx-auto mt-2 max-w-[420px] text-[14px] text-text-muted">
        ScamShield couldn&apos;t complete the investigation. {message}
      </p>
      <button
        type="button"
        onClick={onRetry}
        className="mt-5 inline-flex items-center gap-2 rounded-lg bg-surface px-5 py-2.5 text-[14px] font-semibold text-text transition-colors hover:bg-surface-high"
      >
        <span className="material-symbols-outlined text-[18px]">replay</span>
        Try again
      </button>
    </section>
  );
}
