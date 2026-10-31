import { motion } from "motion/react";
import { ArrowRight, Camera, ChevronDown, ImageIcon, MessageSquareText, QrCode, Upload } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import Dropzone from "./Dropzone";
import QrScanner from "./QrScanner";
import { MODES, MODE_CONFIG } from "../lib/modes";

const EASE = [0.22, 1, 0.36, 1];
const ICONS = { [MODES.TEXT]: MessageSquareText, [MODES.IMAGE]: ImageIcon, [MODES.QR]: QrCode };

const EXAMPLES = [
  { label: "A fake bank message", org: "SBI", text: "Dear customer, your SBI account will be blocked today. Update your KYC immediately: http://sbi-kyc-update.top/login or call 9876543210" },
  { label: "A real bank alert", org: "", text: "Rs 1,200 debited from A/c XX1234 on 12-Mar to VPA store@okaxis. UPI Ref 123456789. Avl Bal Rs 5,000. - SBI" },
  { label: "A real link from a friend", org: "", text: "Check this article https://www.thehindu.com/news/national/ it's interesting" },
  { label: "A dead link", org: "", text: "Please open https://this-shop-doesnt-exist-xyz-123.in/offer to see the deal" },
];

export default function AnalyzeForm({ mode, onMode, onSubmit }) {
  const [message, setMessage] = useState("");
  const [org, setOrg] = useState("");
  const [file, setFile] = useState(null);
  const [showCtx, setShowCtx] = useState(false);
  const [qrSource, setQrSource] = useState("camera");
  const area = useRef(null);

  const usingCamera = mode === MODES.QR && qrSource === "camera";
  const ready = mode === MODES.TEXT ? message.trim().length > 0 : !usingCamera && Boolean(file);

  useEffect(() => {
    const el = area.current;
    if (el) {
      el.style.height = "140px";
      el.style.height = `${Math.min(Math.max(el.scrollHeight + 2, 140), 320)}px`;
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
  useEffect(() => {
    submitRef.current = submit;
  }, [submit]);
  useEffect(() => {
    const onKey = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") submitRef.current(e);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  return (
    <motion.form onSubmit={submit} className="card overflow-hidden" initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.25, ease: EASE }}>
      <div role="tablist" aria-label="What would you like to check?" className="grid grid-cols-3 gap-1 border-b border-line bg-sunken p-1.5">
        {Object.values(MODES).map((m) => {
          const on = mode === m;
          const Icon = ICONS[m];
          return (
            <button key={m} type="button" role="tab" aria-selected={on} onClick={() => { setFile(null); onMode(m); }} className={`relative flex items-center justify-center gap-2 rounded-lg px-2 py-2.5 text-[14px] font-medium transition-colors sm:text-[15px] ${on ? "text-ink" : "text-soft hover:text-ink"}`}>
              {on && <motion.span layoutId="tab-pill" className="absolute inset-0 rounded-lg border border-line bg-card shadow-sm" transition={{ type: "spring", stiffness: 420, damping: 36 }} />}
              <Icon size={17} className="relative hidden sm:block" />
              <span className="relative">{MODE_CONFIG[m].short}</span>
            </button>
          );
        })}
      </div>

      <div className="p-4 sm:p-6">
        {mode === MODES.TEXT && (
          <div>
            <label htmlFor="message" className="mb-2 block font-medium">Paste the message you received</label>
            <textarea id="message" ref={area} value={message} onChange={(e) => setMessage(e.target.value)} maxLength={5000} rows={4} placeholder="SMS, WhatsApp message, email or a link…" className="field block min-h-[140px] resize-none leading-relaxed" />
            <div className="mt-3 flex flex-wrap items-center gap-x-2 gap-y-2">
              <span className="text-[14px] text-soft">Try an example:</span>
              {EXAMPLES.map((ex) => (
                <button key={ex.label} type="button" onClick={() => { setMessage(ex.text); setOrg(ex.org); setShowCtx(Boolean(ex.org)); }} className="rounded-full border border-line bg-card px-3 py-1 text-[13.5px] text-soft transition-colors hover:border-brand hover:text-ink">
                  {ex.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {mode === MODES.IMAGE && <Dropzone file={file} onFile={setFile} title="Drop your screenshot here, or click to choose" subtitle="We'll read the text, links and sender for you." />}

        {mode === MODES.QR && (
          <div>
            <div className="mb-3 inline-flex rounded-lg border border-line p-1 text-[14px]">
              {[["camera", "Use camera", Camera], ["upload", "Upload a picture", Upload]].map(([k, l, Icon]) => (
                <button key={k} type="button" onClick={() => { setQrSource(k); setFile(null); }} className={`inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 transition-colors ${qrSource === k ? "bg-brand-soft font-medium text-brand" : "text-soft hover:text-ink"}`}>
                  <Icon size={15} /> {l}
                </button>
              ))}
            </div>
            {usingCamera ? (
              <QrScanner onDecoded={(text) => onSubmit(mode, { qrText: text, claimedOrganization: org })} />
            ) : (
              <Dropzone file={file} onFile={setFile} title="Drop a picture of the QR code, or click to choose" subtitle="A photo or screenshot works." />
            )}
          </div>
        )}

        <div className="mt-4">
          <button type="button" onClick={() => setShowCtx((v) => !v)} aria-expanded={showCtx} className="inline-flex items-center gap-1 text-[14px] text-soft hover:text-ink">
            <ChevronDown size={16} className={`transition-transform duration-200 ${showCtx ? "rotate-180" : ""}`} /> Who does it claim to be from? <span className="text-faint">(optional)</span>
          </button>
          {showCtx && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} className="overflow-hidden">
              <input aria-label="Organisation the message claims to be from" value={org} onChange={(e) => setOrg(e.target.value)} maxLength={80} placeholder="For example SBI, Amazon or the Income Tax Department" className="field mt-2" />
            </motion.div>
          )}
        </div>

        {!usingCamera && (
          <div className="mt-5">
            <button type="submit" disabled={!ready} className="btn-primary group w-full sm:w-auto sm:min-w-[240px]">
              {MODE_CONFIG[mode].action}
              <ArrowRight size={18} className="transition-transform duration-200 group-hover:translate-x-0.5" />
            </button>
          </div>
        )}
      </div>
    </motion.form>
  );
}
