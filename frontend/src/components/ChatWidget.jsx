import { AnimatePresence, motion } from "motion/react";
import { ArrowUp, MessageCircleQuestion, X } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { askAssistant, summariseResult } from "../lib/chat";

const EASE = [0.16, 1, 0.3, 1];
const GENERAL = [
  "How do I spot a fake KYC message?",
  "I shared my OTP. What should I do now?",
  "What is a digital arrest scam?",
  "Is it safe to scan any QR code?",
];
const ABOUT_RESULT = ["Explain this result in simple words", "What should I do now?"];

export default function ChatWidget({ result }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const abortRef = useRef(null);
  const endRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, error, open]);

  useEffect(() => {
    if (open) inputRef.current?.focus();
    const onKey = (e) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  useEffect(() => () => abortRef.current?.abort(), []);

  const send = useCallback(
    async (text) => {
      const clean = text.trim();
      if (!clean || busy) return;
      setError("");
      setDraft("");
      const next = [...messages, { role: "user", text: clean }];
      setMessages([...next, { role: "assistant", text: "" }]);
      setBusy(true);
      const controller = new AbortController();
      abortRef.current = controller;
      try {
        await askAssistant(next, summariseResult(result), {
          signal: controller.signal,
          onText: (piece) =>
            setMessages((prev) => {
              const copy = [...prev];
              copy[copy.length - 1] = { role: "assistant", text: copy[copy.length - 1].text + piece };
              return copy;
            }),
        });
      } catch (err) {
        if (err.name === "AbortError") return;
        setError(err.message || "The assistant isn't available right now.");
        setMessages((prev) => (prev[prev.length - 1]?.text === "" ? prev.slice(0, -1) : prev));
      } finally {
        setBusy(false);
      }
    },
    [busy, messages, result],
  );

  const suggestions = result ? [...ABOUT_RESULT, ...GENERAL.slice(0, 2)] : GENERAL;

  return (
    <>
      <AnimatePresence>
        {!open && (
          <motion.button
            type="button"
            onClick={() => setOpen(true)}
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 14 }}
            transition={{ duration: 0.5, ease: EASE }}
            aria-label="Ask the ScamShield assistant"
            className="fixed bottom-5 right-4 z-50 flex items-center gap-2.5 border border-[rgb(var(--tint))] bg-ink px-4 py-3 text-[13px] font-semibold uppercase tracking-[0.1em] tint-text shadow-[0_8px_30px_-8px_rgba(0,0,0,0.7)] transition-colors hover:bg-[rgb(var(--tint))] hover:text-ink sm:right-6"
          >
            <MessageCircleQuestion size={18} /> Ask about scams
          </motion.button>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {open && (
          <motion.section
            role="dialog"
            aria-label="ScamShield assistant"
            initial={{ opacity: 0, y: 24, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 24, scale: 0.98 }}
            transition={{ duration: 0.4, ease: EASE }}
            className="fixed inset-x-3 bottom-3 z-50 flex max-h-[min(640px,calc(100dvh-24px))] flex-col border hairline bg-ink-2 shadow-[0_20px_60px_-12px_rgba(0,0,0,0.8)] sm:inset-x-auto sm:bottom-5 sm:right-6 sm:w-[400px]"
          >
            <header className="flex items-start justify-between gap-3 border-b hairline px-4 py-3.5">
              <div>
                <div className="display text-[22px] tracking-wide">Scam assistant</div>
                <p className="text-[12px] text-muted">Ask anything about scams and online safety.</p>
              </div>
              <button type="button" onClick={() => setOpen(false)} aria-label="Close assistant" className="mt-0.5 flex h-8 w-8 items-center justify-center text-muted transition-colors hover:text-text">
                <X size={18} />
              </button>
            </header>

            <div className="min-h-[200px] flex-1 space-y-3 overflow-y-auto px-4 py-4" aria-live="polite">
              {messages.length === 0 && (
                <div>
                  <p className="text-[14px] leading-relaxed text-muted">
                    {result ? "I can see the result you just got, so I can explain it. " : ""}
                    I can't open links myself, so use the checker on this page for those. Please don't share OTPs, PINs or passwords here.
                  </p>
                  <div className="mt-3 flex flex-col gap-2">
                    {suggestions.map((s) => (
                      <button key={s} type="button" onClick={() => send(s)} className="border hairline px-3 py-2 text-left text-[13px] text-text transition-colors hover:border-[rgba(var(--tint),0.6)] hover:bg-[rgba(var(--tint),0.08)]">
                        {s}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((m, i) => (
                <div key={i} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
                  <div className={`max-w-[88%] whitespace-pre-wrap break-words px-3.5 py-2.5 text-[14px] leading-relaxed ${m.role === "user" ? "bg-[rgba(var(--tint),0.16)] text-text" : "border hairline bg-ink-3 text-text"}`}>
                    {m.text || (busy && i === messages.length - 1 ? <span className="inline-flex gap-1" aria-label="Thinking">{[0, 1, 2].map((d) => <motion.span key={d} className="h-1.5 w-1.5 rounded-full bg-muted" animate={{ opacity: [0.25, 1, 0.25] }} transition={{ duration: 1, repeat: Infinity, delay: d * 0.18 }} />)}</span> : "")}
                  </div>
                </div>
              ))}
              {error && <p role="alert" className="text-[13px] text-danger">{error}</p>}
              <div ref={endRef} />
            </div>

            <form onSubmit={(e) => { e.preventDefault(); send(draft); }} className="border-t hairline p-3">
              <div className="flex items-end gap-2">
                <textarea
                  ref={inputRef}
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(draft); } }}
                  rows={1}
                  maxLength={1200}
                  placeholder="Type your question…"
                  aria-label="Your question"
                  className="max-h-28 min-h-[42px] flex-1 resize-none border hairline bg-ink/60 px-3 py-2.5 text-[14px] text-text outline-none placeholder:text-faint focus:border-[rgba(var(--tint),0.6)]"
                />
                <button type="submit" disabled={busy || !draft.trim()} aria-label="Send" className="flex h-[42px] w-[42px] shrink-0 items-center justify-center border border-[rgb(var(--tint))] tint-text transition-colors enabled:hover:bg-[rgb(var(--tint))] enabled:hover:text-ink disabled:opacity-35">
                  <ArrowUp size={18} />
                </button>
              </div>
              <p className="mt-2 text-[11px] leading-snug text-faint">AI can make mistakes. For fraud that has already happened, call 1930 straight away.</p>
            </form>
          </motion.section>
        )}
      </AnimatePresence>
    </>
  );
}
