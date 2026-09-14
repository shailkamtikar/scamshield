export default function Footer() {
  return (
    <footer className="mt-auto border-t border-border bg-surface-inset/60">
      <div className="mx-auto flex max-w-[860px] flex-col items-center justify-between gap-2 px-4 py-6 text-center text-[13px] text-text-muted md:flex-row md:px-8 md:text-left">
        <div className="flex flex-wrap items-center justify-center gap-x-2 gap-y-1 md:justify-start">
          <span>ScamShield</span>
          <span className="text-text-faint">•</span>
          <span>Agentic scam &amp; phishing detection</span>
          <span className="text-text-faint">•</span>
          <span>Final-year project build</span>
        </div>
        <span className="text-text-faint">Built with FastAPI, LangGraph &amp; Gemini</span>
      </div>
    </footer>
  );
}
