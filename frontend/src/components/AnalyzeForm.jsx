import { AnimatePresence, motion } from "motion/react";
import { ArrowRight, ChevronDown, Link2, ScanLine, TriangleAlert } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import Dropzone, { validateImage } from "./Dropzone";
import QrScanner from "./QrScanner";
import { MODES } from "../lib/modes";

const EXAMPLES = [
  { label: "Fake KYC alert", org: "SBI", text: "Dear customer, your SBI account will be blocked today. Update your KYC immediately: http://sbi-kyc-update.top/login or call 9876543210" },
  { label: "Courier fee", org: "", text: "India Post: your parcel could not be delivered. Pay Rs 25 redelivery fee: https://dc9x35ez.top/login" },
  { label: "Genuine bank alert", org: "", text: "Rs 1,200 debited from A/c XX1234 on 12-Mar to VPA store@okaxis. UPI Ref 123456789. Avl Bal Rs 5,000. - SBI" },
  { label: "Link from a friend", org: "", text: "Check this article https://www.thehindu.com/news/national/ it's interesting" },
  { label: "A dead link", org: "", text: "Please open https://this-site-really-doesnt-exist-12345.com to see the offer" },
];

const TAB_ICON = { [MODES.TEXT]: Link2, [MODES.IMAGE]: ScanLine, [MODES.QR]: ScanLine };
const TAB_SHORT = { [MODES.TEXT]: "Message", [MODES.IMAGE]: "Screenshot", [MODES.QR]: "QR code" };
const TAB_LABEL = { [MODES.TEXT]: "Message or link", [MODES.IMAGE]: "Screenshot", [MODES.QR]: "QR code" };
const looksLikeUrl = (s) => /^(https?:\/\/|www\.)\S+$/i.test(s.trim()) || /^[a-z0-9-]+(\.[a-z0-9-]+)+(\/\S*)?$/i.test(s.trim());

export default function AnalyzeForm({ mode, onMode, onSubmit, prefill, engineDown }) {
  const [message, setMessage] = useState("");
  const [org, setOrg] = useState("");
  const [file, setFile] = useState(null);
  const [showCtx, setShowCtx] = useState(false);
  const [qrSource, setQrSource] = useState("camera"); // camera | upload
  const [dragging, setDragging] = useState(false);
  const [dropError, setDropError] = useState("");
  const area = useRef(null);

  const ready = mode === MODES.TEXT ? message.trim().length > 0 : mode === MODES.IMAGE ? Boolean(file) : qrSource === "upload" && Boolean(file);
  const isUrl = mode === MODES.TEXT && looksLikeUrl(message);

  useEffect(() => {
    const el = area.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.min(Math.max(el.scrollHeight, 150), 340)}px`;
    }
  }, [message, mode]);

  // "Try this in the analyzer" from the examples section
  useEffect(() => {
    if (!prefill) return;
    setMessage(prefill.message);
    setOrg(prefill.org || "");
    setShowCtx(Boolean(prefill.org));
    setFile(null);
    onMode(MODES.TEXT);
    const t = setTimeout(() => area.current?.focus({ preventScroll: true }), 400);
    return () => clearTimeout(t);
  }, [prefill]); // eslint-disable-line react-hooks/exhaustive-deps

  const submit = useCallback(
    (e) => {
      e?.preventDefault();
      if (!ready) return;
      if (mode === MODES.TEXT) onSubmit(mode, { message: message.trim(), claimedOrganization: org });
      else onSubmit(mode, { file, claimedOrganization: org });
    },
    [ready, mode, message, file, org, onSubmit],
  );

  const submitRef = useRef(submit);
  submitRef.current = submit;
  useEffect(() => {
    const onKey = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") submitRef.current(e);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const switchMode = (m) => {
    setFile(null);
    setDropError("");
    onMode(m);
  };

  // dropping an image anywhere on the card switches to screenshot mode
  const onDragOver = (e) => {
    if ([...(e.dataTransfer?.types || [])].includes("Files") && mode === MODES.TEXT) {
      e.preventDefault();
      setDragging(true);
    }
  };
  const onDrop = (e) => {
    if (mode !== MODES.TEXT) return;
    const f = e.dataTransfer?.files?.[0];
    setDragging(false);
    if (!f) return;
    e.preventDefault();
    const problem = validateImage(f);
    if (problem) { setDropError(problem); return; }
    setDropError("");
    onMode(MODES.IMAGE);
    setFile(f);
  };

  return (
    <motion.form
      onSubmit={submit}
      onDragOver={onDragOver}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      className="surface relative overflow-hidden shadow-[0_40px_120px_-40px_rgba(0,0,0,0.9)]"
      initial={{ opacity: 0, y: 28 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 1, delay: 0.55, ease: [0.16, 1, 0.3, 1] }}
      aria-label="Check something"
    >
      <div role="tablist" aria-label="What do you want to check?" className="flex gap-1 border-b border-line p-2">
        {Object.values(MODES).map((m) => {
          const on = mode === m;
          const Icon = TAB_ICON[m];
          return (
            <button
              key={m} type="button" role="tab" aria-selected={on} onClick={() => switchMode(m)}
              className={`relative flex flex-1 items-center justify-center gap-2 rounded-lg px-2 py-2.5 text-[13.5px] font-medium transition-colors sm:flex-none sm:px-5 ${on ? "text-text" : "text-faint hover:text-muted"}`}
            >
              {on && <motion.span layoutId="tab-pill" className="absolute inset-0 rounded-lg bg-white/[0.06] ring-1 ring-inset ring-white/10" transition={{ type: "spring", stiffness: 420, damping: 36 }} />}
              <Icon size={15} className="relative hidden sm:block" /> <span className="relative whitespace-nowrap">{TAB_SHORT[m]}<span className="hidden sm:inline">{TAB_LABEL[m].slice(TAB_SHORT[m].length)}</span></span>
            </button>
          );
        })}
      </div>

      <div className="p-4 sm:p-5">
        {engineDown && (
          <div role="alert" className="mb-4 flex items-start gap-2.5 rounded-lg border border-[rgba(255,176,32,0.35)] bg-[rgba(255,176,32,0.07)] px-3.5 py-2.5 text-[13.5px] text-warn">
            <TriangleAlert size={16} className="mt-0.5 shrink-0" /> The analysis service is not reachable right now. You can still type, but the check will fail until it is back.
          </div>
        )}

        {mode === MODES.TEXT && (
          <div>
            <div className="rounded-xl border border-line-strong bg-ink/70 transition-[border-color,box-shadow] duration-300 focus-within:border-[rgba(var(--tint),0.55)] focus-within:shadow-[0_0_0_4px_rgba(var(--tint),0.08)]">
              <textarea
                ref={area} value={message} onChange={(e) => setMessage(e.target.value)} maxLength={40000} rows={5}
                placeholder="Paste a suspicious SMS, WhatsApp message, email or link…"
                aria-label="Message or link to check"
                className="block min-h-[150px] w-full resize-none bg-transparent p-4 text-[16px] leading-relaxed text-text outline-none placeholder:text-faint"
              />
              <div className="flex items-center justify-between gap-3 border-t border-line px-4 py-2.5">
                <span className="flex items-center gap-2 text-[12.5px] text-faint">
                  <AnimatePresence mode="wait" initial={false}>
                    {isUrl ? (
                      <motion.span key="url" initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }} className="inline-flex items-center gap-1.5 tint-text"><Link2 size={13} /> Link detected. We will follow it safely, never on your device.</motion.span>
                    ) : (
                      <motion.span key="hint" initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }}>Drop or paste a screenshot, or a whole email with its headers.</motion.span>
                    )}
                  </AnimatePresence>
                </span>
                <span className="hidden font-mono text-[11px] text-faint sm:block">{message.length.toLocaleString()} / 40,000</span>
              </div>
            </div>
            {dropError && <p role="alert" className="mt-2 text-[13px] text-danger">{dropError}</p>}
            <div className="mt-3.5 flex flex-wrap items-center gap-2">
              <span className="mr-1 text-[12.5px] text-faint">Try an example</span>
              {EXAMPLES.map((ex) => (
                <button
                  key={ex.label} type="button"
                  onClick={() => { setMessage(ex.text); setOrg(ex.org); setShowCtx(Boolean(ex.org)); area.current?.focus(); }}
                  className="rounded-full border border-line-strong px-3 py-1 text-[12.5px] text-muted transition-colors hover:border-[rgba(var(--tint),0.5)] hover:text-text"
                >
                  {ex.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {mode === MODES.IMAGE && <Dropzone file={file} onFile={setFile} title="Drop a screenshot here" subtitle="We read its text, links and sender, then check them." />}

        {mode === MODES.QR && (
          <div>
            <div className="mb-3 inline-flex rounded-lg border border-line-strong p-0.5 text-[13px]">
              {[["camera", "Use camera"], ["upload", "Upload image"]].map(([k, l]) => (
                <button key={k} type="button" onClick={() => { setQrSource(k); setFile(null); }} className={`rounded-md px-4 py-1.5 transition-colors ${qrSource === k ? "bg-white/[0.07] text-text" : "text-muted hover:text-text"}`}>
                  {l}
                </button>
              ))}
            </div>
            {qrSource === "camera" ? (
              <QrScanner onDecoded={(text) => onSubmit(mode, { qrText: text, claimedOrganization: org })} onUnavailable={() => {}} />
            ) : (
              <Dropzone file={file} onFile={setFile} title="Drop a QR code image" subtitle="A photo or screenshot that contains a QR code. The link inside is never opened." />
            )}
          </div>
        )}

        <div className="mt-4 flex flex-col-reverse gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div className="min-w-0 sm:max-w-[380px]">
            <button type="button" onClick={() => setShowCtx((v) => !v)} className="inline-flex items-center gap-1.5 text-[13px] text-muted transition-colors hover:text-text" aria-expanded={showCtx}>
              <ChevronDown size={14} className={`transition-transform ${showCtx ? "rotate-180" : ""}`} /> Who is it from? <span className="text-faint">(optional)</span>
            </button>
            <AnimatePresence initial={false}>
              {showCtx && (
                <motion.label initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} className="mt-2.5 block overflow-hidden">
                  <input value={org} onChange={(e) => setOrg(e.target.value)} maxLength={80} placeholder="e.g. SBI, Amazon, Income Tax Department" aria-label="Organisation the message claims to be from"
                    className="w-full rounded-lg border border-line-strong bg-ink/70 px-3 py-2.5 text-[14px] outline-none transition-colors placeholder:text-faint focus:border-[rgba(var(--tint),0.55)]" />
                </motion.label>
              )}
            </AnimatePresence>
          </div>

          {!(mode === MODES.QR && qrSource === "camera") && (
            <div className="flex items-center gap-4 sm:justify-end">
              <span className="hidden text-[12px] text-faint lg:block">Ctrl + Enter</span>
              <button type="submit" disabled={!ready} className="btn-primary group w-full sm:w-auto sm:min-w-[190px]">
                <span>Analyse</span>
                <ArrowRight size={17} className="transition-transform duration-300 group-enabled:group-hover:translate-x-1" />
              </button>
            </div>
          )}
        </div>
      </div>

      <AnimatePresence>
        {dragging && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center bg-ink/85 backdrop-blur-sm">
            <div className="rounded-xl border border-dashed border-[rgba(var(--tint),0.7)] px-8 py-6 text-center">
              <ScanLine size={26} className="tint-text mx-auto mb-2" />
              <p className="display text-[1.7rem]">Drop to scan this screenshot</p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.form>
  );
}
