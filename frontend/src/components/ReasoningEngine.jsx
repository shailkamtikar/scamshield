import { formatModelName, isFallbackModel, PRIMARY_MODEL_ID, SECONDARY_MODEL_ID } from "../lib/reasoningModel";

/**
 * Shows which Gemini model actually produced this result. Only labels a
 * result as "fallback engine used" when the backend's real `reasoning_model`
 * value says so — never assumed.
 */
export default function ReasoningEngine({ reasoningModel }) {
  const usedFallback = isFallbackModel(reasoningModel);

  return (
    <section className="rounded-2xl bg-surface p-4 shadow-[var(--shadow-card)]">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-accent/10 text-accent">
            <span className="material-symbols-outlined text-[18px]">neurology</span>
          </span>
          <div>
            <span className="block text-[11px] font-semibold uppercase tracking-wider text-text-muted">
              Reasoning Engine
            </span>
            <span className="block text-[14px] font-medium text-text">
              {formatModelName(reasoningModel) || "Not reported"}
            </span>
          </div>
        </div>

        {usedFallback && (
          <span className="inline-flex items-center gap-1 rounded-full bg-risk-medium-bg px-2.5 py-1 text-[11px] font-semibold text-risk-medium">
            <span className="material-symbols-outlined text-[14px]">sync_alt</span>
            Fallback engine used
          </span>
        )}
      </div>

      <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 font-mono text-[11px] text-text-faint">
        <span>PRIMARY: {formatModelName(PRIMARY_MODEL_ID)}</span>
        <span>FALLBACK: {formatModelName(SECONDARY_MODEL_ID)}</span>
      </div>
    </section>
  );
}
