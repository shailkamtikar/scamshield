import { motion } from "motion/react";
import { ArrowRight, ChevronDown } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import Dropzone from "./Dropzone";
import QrScanner from "./QrScanner";
import { MODES, MODE_CONFIG } from "../lib/modes";

const EXAMPLES = [
  { label: "Fake KYC scam", org: "SBI", text: "Dear customer, your SBI account will be blocked today. Update your KYC immediately: http://sbi-kyc-update.top/login or call 9876543210" },
  { label: "Genuine bank alert", org: "", text: "Rs 1,200 debited from A/c XX1234 on 12-Mar to VPA store@okaxis. UPI Ref 123456789. Avl Bal Rs 5,000. - SBI" },
  { label: "Real link from a friend", org: "", text: "Check this article https://www.thehindu.com/news/national/ it's interesting" },
  { label: "Dead link", org: "", text: "Please open https://this-site-really-doesnt-exist-12345.com to see the offer" },
  { label: "Courier fee scam", org: "", text: "India Post: your parcel could not be delivered. Pay Rs 25 redelivery fee: https://dc9x35ez.top/login" },
];

export default function AnalyzeForm({ mode, onMode, onSubmit }) {
  const [message, setMessage] = useState("");
  const [org, setOrg] = useState("");
  const [file, setFile] = useState(null);
  const [showCtx, setShowCtx] = useState(false);
  const [qrSource, setQrSource] = useState("camera"); // camera | upload
  const [examples, setExamples] = useState(false);
  const area = useRef(null);

  const ready = mode === MODES.TEXT ? message.trim().length > 0 : mode === MODES.IMAGE ? Boolean(file) : qrSource === "upload" && Boolean(file);

  useEffect(() => {
    const el = area.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 340)}px`;
    }
  }, [message]);

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
    onMode(m);
  };

  return (
    <motion.form
      onSubmit={submit}
      className="border hairline bg-ink-2/70 backdrop-blur-sm"
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.9, delay: 0.7, ease: [0.16, 1, 0.3, 1] }}
    >
      <div role="tablist" aria-label="Input type" className="grid grid-cols-3 border-b hairline">
        {Object.values(MODES).map((m) => {
          const on = mode === m;
          return (
            <button
              key={m}
              type="button"
              role="tab"
              aria-selected={on}
              onClick={() => switchMode(m)}
              className={`relative px-4 py-4 text-left transition-colors sm:px-6 ${on ? "text-text" : "text-faint hover:text-muted"}`}
            >
              <span className="label !text-inherit">{MODE_CONFIG[m].no}</span>
              <span className="display mt-1 block text-[clamp(1.1rem,3.2vw,1.8rem)]">{MODE_CONFIG[m].label}</span>
              {on && <motion.span layoutId="tab-underline" className="absolute inset-x-0 bottom-[-1px] h-[2px] bg-[rgb(var(--tint))]" transition={{ type: "spring", stiffness: 380, damping: 34 }} />}
            </button>
          );
        })}
      </div>

      <div className="p-4 sm:p-6">
        <p className="label mb-3 !normal-case !tracking-wider">{MODE_CONFIG[mode].hint}</p>

        {mode === MODES.TEXT && (
          <div>
            <textarea
              ref={area}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              maxLength={5000}
              rows={5}
              placeholder="Paste the suspicious message here…"
              aria-label="Message to check"
              className="block min-h-[150px] w-full resize-none border hairline bg-ink/60 p-4 text-[15px] leading-relaxed text-text outline-none transition-colors placeholder:text-faint focus:border-[rgba(var(--tint),0.6)]"
            />
            <div className="mt-2 flex items-center justify-between">
              <span className="font-mono text-[11px] text-faint">{message.length.toLocaleString()} / 5,000</span>
              <div className="relative">
                <button type="button" onClick={() => setExamples((v) => !v)} className="inline-flex items-center gap-1 font-mono text-[11px] tint-text hover:underline" aria-expanded={examples}>
                  Try an example <ChevronDown size={12} className={examples ? "rotate-180 transition-transform" : "transition-transform"} />
                </button>
                {examples && (
                  <motion.ul initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} className="absolute right-0 top-full z-10 mt-2 w-64 border hairline bg-ink-2 shadow-2xl">
                    {EXAMPLES.map((ex) => (
                      <li key={ex.label}>
                        <button type="button" onClick={() => { setMessage(ex.text); setOrg(ex.org); setShowCtx(Boolean(ex.org)); setExamples(false); }} className="block w-full px-4 py-2.5 text-left text-[13px] text-muted transition-colors hover:bg-ink-3 hover:text-text">
                          {ex.label}
                        </button>
                      </li>
                    ))}
                  </motion.ul>
                )}
              </div>
            </div>
          </div>
        )}

        {mode === MODES.IMAGE && <Dropzone file={file} onFile={setFile} title="Drop a screenshot" subtitle="We read the text, links and sender, then check them." />}

        {mode === MODES.QR && (
          <div>
            <div className="mb-3 inline-flex border hairline text-[12px]">
              {[["camera", "Camera"], ["upload", "Upload image"]].map(([k, l]) => (
                <button key={k} type="button" onClick={() => { setQrSource(k); setFile(null); }} className={`px-4 py-1.5 transition-colors ${qrSource === k ? "bg-[rgba(var(--tint),0.14)] tint-text" : "text-muted hover:text-text"}`}>
                  {l}
                </button>
              ))}
            </div>
            {qrSource === "camera" ? (
              <QrScanner onDecoded={(text) => onSubmit(mode, { qrText: text, claimedOrganization: org })} onUnavailable={() => {}} />
            ) : (
              <Dropzone file={file} onFile={setFile} title="Drop a QR image" subtitle="A photo or screenshot containing a QR code." />
            )}
          </div>
        )}

        <div className="mt-5 border-t hairline pt-4">
          <button type="button" onClick={() => setShowCtx((v) => !v)} className="label inline-flex items-center gap-1.5 hover:text-text" aria-expanded={showCtx}>
            <ChevronDown size={12} className={showCtx ? "rotate-180 transition-transform" : "transition-transform"} /> Add context (optional)
          </button>
          {showCtx && (
            <motion.label initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} className="mt-3 block overflow-hidden">
              <span className="mb-1.5 block text-[12px] text-muted">Who does the message claim to be from?</span>
              <input value={org} onChange={(e) => setOrg(e.target.value)} maxLength={80} placeholder="e.g. SBI, Amazon, Income Tax Department" className="w-full border hairline bg-ink/60 px-3 py-2.5 text-[14px] outline-none placeholder:text-faint focus:border-[rgba(var(--tint),0.6)]" />
            </motion.label>
          )}
        </div>

        {!(mode === MODES.QR && qrSource === "camera") && (
          <div className="mt-5 flex items-center justify-between gap-4">
            <span className="label hidden sm:block !text-[10px]">Ctrl + Enter to analyse</span>
            <button
              type="submit"
              disabled={!ready}
              className="group relative ml-auto inline-flex w-full items-center justify-between gap-6 overflow-hidden border border-[rgb(var(--tint))] px-6 py-3.5 text-[14px] font-semibold tint-text transition-all enabled:hover:text-ink disabled:cursor-not-allowed disabled:opacity-35 sm:w-auto sm:min-w-[260px]"
            >
              <span className="absolute inset-0 -z-0 origin-left scale-x-0 bg-[rgb(var(--tint))] transition-transform duration-500 ease-[var(--ease-out-expo)] group-enabled:group-hover:scale-x-100" />
              <span className="relative z-10 uppercase tracking-[0.12em]">Analyse</span>
              <ArrowRight size={18} className="relative z-10 transition-transform group-enabled:group-hover:translate-x-1" />
            </button>
          </div>
        )}
      </div>
    </motion.form>
  );
}
