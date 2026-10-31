import { animate, AnimatePresence, motion, useReducedMotion } from "motion/react";
import { Check, ChevronDown, Copy, Download, Eye, EyeOff, RotateCcw } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { MODE_CONFIG, MODES } from "../lib/modes";
import { TRUST_LABEL, getVerdict } from "../lib/verdict";
import { ageLabel, defang, shortUrl } from "../lib/format";

const EASE = [0.16, 1, 0.3, 1];
const reveal = (i = 0) => ({ initial: { opacity: 0, y: 28 }, whileInView: { opacity: 1, y: 0 }, viewport: { once: true, margin: "-60px" }, transition: { duration: 0.8, delay: i * 0.06, ease: EASE } });

function CountUp({ value, suffix = "", duration = 1.4 }) {
  const reduce = useReducedMotion();
  const [n, setN] = useState(reduce ? value : 0);
  useEffect(() => {
    if (reduce) { setN(value); return undefined; }
    const controls = animate(0, value, { duration, ease: EASE, onUpdate: (v) => setN(Math.round(v)) });
    return () => controls.stop();
  }, [value, duration, reduce]);
  return <>{n}{suffix}</>;
}

function Section({ no, title, children, i = 0 }) {
  return (
    <motion.section {...reveal(i)} className="border-t hairline py-10 sm:py-14">
      <div className="mb-6 flex items-baseline gap-4">
        <span className="font-mono text-[12px] tint-text">{no}</span>
        <h3 className="display text-[clamp(1.8rem,4.5vw,3rem)]">{title}</h3>
      </div>
      {children}
    </motion.section>
  );
}

/* -------------------------------------------------------------- verdict hero */
function ScoreBar({ score, verdict }) {
  const left = verdict === "COULD_NOT_VERIFY" ? 0 : Math.max(2, Math.min(98, score));
  return (
    <div>
      <div className="relative h-[10px] w-full" aria-hidden>
        <div className="absolute inset-0 flex gap-[3px]">
          <div className="h-full flex-[20] bg-safe/35" /><div className="h-full flex-[40] bg-warn/35" /><div className="h-full flex-[40] bg-danger/35" />
        </div>
        {verdict !== "COULD_NOT_VERIFY" && (
          <motion.div className="absolute -top-[7px] h-[24px] w-[3px] bg-white shadow-[0_0_14px_rgba(255,255,255,0.8)]" initial={{ left: "0%" }} animate={{ left: `${left}%` }} transition={{ duration: 1.5, delay: 0.5, ease: EASE }} />
        )}
      </div>
      <div className="mt-2 flex justify-between font-mono text-[10px] text-faint"><span>0 SAFE</span><span>20 SUSPICIOUS</span><span>60 DANGEROUS 100</span></div>
    </div>
  );
}

function VerdictHero({ result, meta, onToggleFactors, factorsOpen }) {
  const v = getVerdict(result.verdict);
  const conf = Math.round((result.confidence ?? 0) * 100);
  const f = result.confidence_factors || {};
  return (
    <div className="pt-4 sm:pt-8">
      <div className="label mb-4 flex flex-wrap items-center gap-x-5 gap-y-1">
        <span className="flex items-center gap-3"><span className="inline-block h-px w-8 bg-[rgb(var(--tint))]" />Report</span>
        <span>{meta.ref}</span><span>{MODE_CONFIG[meta.mode].label}</span><span>{(meta.latencyMs / 1000).toFixed(1)}s</span>
      </div>
      <h2 className="text-[clamp(3.6rem,15vw,13rem)]" aria-label={`Verdict: ${v.word}`}>
        <span className="block overflow-hidden pb-[0.05em]">
          <motion.span className="display block" style={{ color: v.color }} initial={{ y: "108%" }} animate={{ y: 0 }} transition={{ duration: 1.1, ease: EASE }}>{v.word}</motion.span>
        </span>
      </h2>
      <motion.p className="mt-3 max-w-[640px] text-[clamp(1.1rem,2.6vw,1.6rem)] font-medium leading-snug" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5, duration: 0.8, ease: EASE }}>
        {v.headline} <span className="text-muted">{v.blurb}</span>
      </motion.p>

      <motion.div className="mt-10 grid gap-px border hairline bg-line sm:grid-cols-[1.4fr_1fr]" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.7, duration: 0.8, ease: EASE }}>
        <div className="bg-ink-2/80 p-5 sm:p-7">
          <div className="label mb-2">Risk score</div>
          <div className="mb-5 flex items-baseline gap-2">
            <span className="display text-[clamp(3.5rem,8vw,6rem)]" style={{ color: v.color }}>{result.verdict === "COULD_NOT_VERIFY" ? "—" : <CountUp value={result.risk_score} />}</span>
            <span className="font-mono text-[13px] text-faint">/ 100</span>
          </div>
          <ScoreBar score={result.risk_score} verdict={result.verdict} />
        </div>
        <div className="bg-ink-2/80 p-5 sm:p-7">
          <div className="label mb-2">Confidence</div>
          <div className="display mb-3 text-[clamp(3.5rem,8vw,6rem)]"><CountUp value={conf} suffix="%" /></div>
          <div className="h-[3px] w-full bg-line"><motion.div className="h-full bg-[rgb(var(--tint))]" initial={{ width: 0 }} animate={{ width: `${conf}%` }} transition={{ duration: 1.4, delay: 0.6, ease: EASE }} /></div>
          <button type="button" onClick={onToggleFactors} aria-expanded={factorsOpen} className="mt-4 inline-flex items-center gap-1 font-mono text-[11px] text-muted hover:text-text">
            How is this calculated? <ChevronDown size={12} className={factorsOpen ? "rotate-180 transition-transform" : "transition-transform"} />
          </button>
          <AnimatePresence>
            {factorsOpen && (
              <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
                <p className="pt-3 text-[12.5px] leading-relaxed text-muted">
                  Confidence comes from the evidence, not from an AI guess: <b className="text-text">{Math.round((f.coverage ?? 0) * 100)}%</b> of the applicable checks completed and{" "}
                  <b className="text-text">{Math.round((f.agreement ?? 0) * 100)}%</b> of the strong evidence points the same way.
                  {f.missing_checks?.length > 0 && <> Unavailable right now: {f.missing_checks.join(", ").replaceAll("_", " ")}.</>}
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  );
}

/* ------------------------------------------------------------------ pieces */
function Reasons({ result }) {
  return (
    <ol className="divide-y divide-line border-y hairline">
      {result.reasons.map((r, i) => (
        <motion.li key={i} {...reveal(i)} className="grid grid-cols-[2.5rem_1fr] gap-3 py-4 sm:grid-cols-[3.5rem_1fr]">
          <span className="font-mono text-[12px] text-faint">{String(i + 1).padStart(2, "0")}</span>
          <p className="text-[15px] leading-relaxed sm:text-[16px]">{r}</p>
        </motion.li>
      ))}
      <li className="flex flex-wrap items-center gap-3 py-3 font-mono text-[11px] text-faint">
        <span>{result.reasoning_model ? `Explained by ${result.reasoning_model}` : "Explained by built-in rules"}</span>
        {result.scam_type && result.scam_type.toLowerCase() !== "none" && <span className="border hairline px-2 py-0.5">{result.scam_type}</span>}
        <span>· Verdict &amp; score are computed by deterministic rules, not by the AI.</span>
      </li>
    </ol>
  );
}

function Field({ k, children }) {
  return (
    <div className="bg-ink-2/80 px-4 py-3">
      <div className="label !text-[10px] mb-1">{k}</div>
      <div className="text-[13px] leading-snug text-text">{children}</div>
    </div>
  );
}

const providerColor = { hit: "bg-danger", clean: "bg-safe", unavailable: "bg-faint", skipped: "bg-faint" };

function InspectionCard({ u, index, nested = false }) {
  const [reveal_, setReveal] = useState(false);
  const v = getVerdict(u.verdict);
  const shown = reveal_ ? u.url : defang(u.url);
  const chain = u.reachability?.chain || [];
  const r = u.reachability;
  const risk = u.signals.filter((s) => s.polarity === "risk");
  const trust = u.signals.filter((s) => s.polarity === "trust");
  return (
    <motion.article {...(nested ? {} : reveal(index))} className="border hairline bg-ink-2/60" style={{ borderLeft: `3px solid ${v.color}` }}>
      <div className="flex flex-wrap items-start justify-between gap-3 p-4 sm:p-5">
        <div className="min-w-0 flex-1">
          <div className="label mb-1">{nested ? "Final destination" : `Inspection ${String(index + 1).padStart(2, "0")}`}</div>
          <p className="break-all font-mono text-[13px] text-text">{shortUrl(shown, 120)}</p>
          <button type="button" onClick={() => setReveal((x) => !x)} className="mt-1.5 inline-flex items-center gap-1 font-mono text-[11px] text-faint hover:text-text">
            {reveal_ ? <EyeOff size={12} /> : <Eye size={12} />} {reveal_ ? "Hide real link" : "Show real link (never click suspicious links)"}
          </button>
        </div>
        <div className="text-right">
          <div className="display text-[26px]" style={{ color: v.color }}>{v.word}</div>
          {u.score != null && <div className="font-mono text-[11px] text-faint">score {u.score}/100</div>}
        </div>
      </div>

      <div className="grid gap-px border-t hairline bg-line sm:grid-cols-2 lg:grid-cols-4">
        <Field k="Trust">{TRUST_LABEL[u.trust.tier]}{u.trust.brand && <span className="text-muted"> · {u.trust.brand}</span>}</Field>
        <Field k="Domain age">{ageLabel(u.domain_age_days) || <span className="text-faint">not available</span>}</Field>
        <Field k="Reachability">
          {r ? <>{r.outcome.replaceAll("_", " ").toLowerCase()}{r.status ? ` (${r.status})` : ""}{chain.length > 1 && <span className="text-muted"> · {chain.length - 1} redirect{chain.length > 2 ? "s" : ""}</span>}</> : <span className="text-faint">not checked</span>}
        </Field>
        <Field k="Threat feeds">
          {u.reputation.length ? (
            <span className="flex flex-wrap gap-x-3 gap-y-1">
              {u.reputation.map((p) => (
                <span key={p.provider} className="inline-flex items-center gap-1.5 text-[12px]" title={p.detail}>
                  <span className={`h-1.5 w-1.5 rounded-full ${providerColor[p.status]}`} />{p.provider.replace("Google ", "")}
                </span>
              ))}
            </span>
          ) : <span className="text-faint">not checked</span>}
        </Field>
      </div>

      {(risk.length > 0 || trust.length > 0) && (
        <ul className="space-y-1.5 border-t hairline p-4 text-[13px] sm:p-5">
          {risk.map((s) => <li key={s.id + s.target} className="flex gap-2"><span className="mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full bg-danger" /><span className="text-muted">{s.explanation}</span></li>)}
          {trust.map((s) => <li key={s.id + s.target} className="flex gap-2"><span className="mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full bg-safe" /><span className="text-muted">{s.explanation}</span></li>)}
        </ul>
      )}
      {u.destination && <div className="border-t hairline p-3 sm:p-4"><InspectionCard u={u.destination} index={0} nested /></div>}
    </motion.article>
  );
}

function QrCard({ qr, decoded }) {
  const [show, setShow] = useState(false);
  if (!qr) return null;
  const s = qr.summary;
  return (
    <motion.div {...reveal()} className="mb-6 border hairline bg-ink-2/60">
      <div className="grid gap-px bg-line sm:grid-cols-3">
        <Field k="QR contains">{qr.title}</Field>
        {qr.service && <Field k="Verified service">{qr.service.name}</Field>}
        {s && (<>
          <Field k="Payee name">{s.payee || "—"}</Field>
          <Field k="Payment address (VPA)"><span className="break-all font-mono text-[12px]">{s.vpa || "—"}</span></Field>
          <Field k="Amount">{s.amount ? `₹ ${s.amount}` : "Not preset — you choose"}</Field>
          <Field k="Note">{s.note || "—"}</Field>
        </>)}
      </div>
      {s && <p className="border-t hairline p-4 text-[13px] text-muted">Scanning a payment QR sends money <b className="text-text">out</b>. You never need to scan a QR or enter your UPI PIN to <i>receive</i> money. Confirm the payee name before paying.</p>}
      <div className="border-t hairline p-4">
        <button type="button" onClick={() => setShow((x) => !x)} className="font-mono text-[11px] text-faint hover:text-text">{show ? "Hide" : "Show"} raw QR content (text only, never opened)</button>
        {show && <pre className="mt-2 whitespace-pre-wrap break-all font-mono text-[12px] text-muted">{decoded}</pre>}
      </div>
    </motion.div>
  );
}

function Evidence({ result }) {
  const [open, setOpen] = useState(false);
  const rows = result.score_breakdown || [];
  return (
    <div>
      <div className="mb-4 divide-y divide-line border-y hairline">
        {rows.length === 0 && <p className="py-4 text-[14px] text-muted">No risk or trust signals were produced.</p>}
        {rows.map((r) => (
          <div key={r.signal} className="flex items-center justify-between gap-4 py-3 text-[14px]">
            <span>{r.signal}</span>
            <span className={`font-mono text-[12px] ${r.points > 0 ? "text-danger" : "text-safe"}`}>{r.points > 0 ? "+" : ""}{r.points}</span>
          </div>
        ))}
      </div>
      <button type="button" onClick={() => setOpen((x) => !x)} aria-expanded={open} className="inline-flex items-center gap-1.5 font-mono text-[11px] text-muted hover:text-text">
        <ChevronDown size={12} className={open ? "rotate-180 transition-transform" : "transition-transform"} /> Full technical trail ({result.evidence.length})
      </button>
      <AnimatePresence>
        {open && (
          <motion.ul initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="mt-3 space-y-2 overflow-hidden font-mono text-[12px] leading-relaxed text-muted">
            {result.evidence.map((e, i) => <li key={i}>› {e}</li>)}
            <li className="pt-2 text-faint">Decision path: {result.decision_path.join(" → ") || "—"} · weights v{result.weights_version}</li>
          </motion.ul>
        )}
      </AnimatePresence>
    </div>
  );
}

function Entities({ entities }) {
  const groups = [["phones", "Phone numbers"], ["upi_ids", "UPI IDs"], ["emails", "Emails"]].filter(([k]) => entities?.[k]?.length);
  if (!groups.length) return null;
  return (
    <div className="mb-6 grid gap-px border hairline bg-line sm:grid-cols-3">
      {groups.map(([k, label]) => <Field key={k} k={`${label} found`}><span className="break-all font-mono text-[12px]">{entities[k].join(", ")}</span></Field>)}
    </div>
  );
}

/* ------------------------------------------------------------------ result */
export default function Result({ meta, imageUrl, onReset }) {
  const { result } = meta;
  const [factors, setFactors] = useState(false);
  const [copied, setCopied] = useState(false);
  const [pdfBusy, setPdfBusy] = useState(false);
  const v = getVerdict(result.verdict);
  const top = useRef(null);
  useEffect(() => {
    top.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, []);

  const summary = () =>
    [`ScamShield: ${v.word.toUpperCase()}${result.verdict === "COULD_NOT_VERIFY" ? "" : ` (risk ${result.risk_score}/100, ${Math.round(result.confidence * 100)}% confidence)`}`, "", ...result.reasons.map((r) => `- ${r}`), "", `What to do: ${result.recommendation}`].join("\n");

  const copy = async () => {
    try { await navigator.clipboard.writeText(summary()); setCopied(true); setTimeout(() => setCopied(false), 2000); } catch { /* clipboard unavailable */ }
  };
  const pdf = async () => {
    setPdfBusy(true);
    try { const { generateReportPdf } = await import("../lib/pdf"); generateReportPdf(meta); } finally { setPdfBusy(false); }
  };

  const showText = meta.mode === MODES.IMAGE && result.extracted_text;

  return (
    <div ref={top} className="scroll-mt-20">
      <VerdictHero result={result} meta={meta} factorsOpen={factors} onToggleFactors={() => setFactors((x) => !x)} />

      <div className="mt-14">
        <Section no="01" title="Why this verdict" i={0}>
          <Reasons result={result} />
        </Section>

        {(result.urls.length > 0 || result.qr) && (
          <Section no="02" title={result.urls.length > 1 ? "Link inspections" : result.qr ? "What the QR does" : "Link inspection"} i={1}>
            <QrCard qr={result.qr} decoded={result.decoded_text} />
            <Entities entities={result.entities} />
            <div className="space-y-4">
              {result.urls.map((u, i) => <InspectionCard key={u.url} u={u} index={i} />)}
            </div>
            {result.skipped_urls?.length > 0 && <p className="mt-3 text-[12px] text-faint">{result.skipped_urls.length} more link(s) were not analysed (limit 6 per check).</p>}
          </Section>
        )}

        {!result.urls.length && !result.qr && (
          <Section no="02" title="What we found" i={1}>
            <Entities entities={result.entities} />
            <p className="text-[15px] text-muted">There were no links in this content, so the verdict is based on the wording alone.</p>
          </Section>
        )}

        {(showText || meta.mode === MODES.TEXT) && (
          <Section no="03" title={showText ? "Text we read" : "Your message"} i={2}>
            <div className="flex flex-col gap-5 sm:flex-row">
              {imageUrl && <img src={imageUrl} alt="Uploaded screenshot" className="h-40 w-40 shrink-0 border hairline bg-ink-3 object-contain" />}
              <div className="min-w-0 flex-1">
                <p className="whitespace-pre-wrap break-words font-mono text-[13px] leading-relaxed text-muted">{showText ? result.extracted_text : meta.input.message}</p>
                {result.extraction && <p className="mt-3 font-mono text-[11px] text-faint">Read by {result.extraction.method.replace("+", " + ")}{result.extraction.sender ? ` · sender: ${result.extraction.sender}` : ""}</p>}
              </div>
            </div>
          </Section>
        )}

        <Section no={showText || meta.mode === MODES.TEXT ? "04" : "03"} title="Evidence" i={3}><Evidence result={result} /></Section>

        <Section no={showText || meta.mode === MODES.TEXT ? "05" : "04"} title="What to do next" i={4}>
          <motion.div {...reveal()} className="border tint-border tint-bg p-6 sm:p-8">
            <p className="max-w-[760px] text-[clamp(1.1rem,2.4vw,1.5rem)] font-medium leading-snug">{result.recommendation}</p>
            {result.verdict !== "SAFE" && <p className="mt-4 font-mono text-[12px] text-muted">Report cyber fraud: cybercrime.gov.in · Helpline 1930 (24×7)</p>}
          </motion.div>
        </Section>
      </div>

      <div className="flex flex-col gap-3 border-t hairline py-8 sm:flex-row sm:items-center sm:justify-between">
        <button type="button" onClick={onReset} className="group inline-flex items-center justify-center gap-2 border border-[rgb(var(--tint))] px-6 py-3 text-[13px] font-semibold uppercase tracking-[0.12em] tint-text transition-colors hover:bg-[rgb(var(--tint))] hover:text-ink">
          <RotateCcw size={15} className="transition-transform group-hover:-rotate-90" /> Check something else
        </button>
        <div className="flex flex-col gap-3 sm:flex-row">
          <button type="button" onClick={copy} className="inline-flex items-center justify-center gap-2 border hairline px-5 py-3 text-[13px] text-muted transition-colors hover:border-line-strong hover:text-text">
            {copied ? <Check size={15} /> : <Copy size={15} />} {copied ? "Copied" : "Copy summary"}
          </button>
          <button type="button" onClick={pdf} disabled={pdfBusy} className="inline-flex items-center justify-center gap-2 border hairline px-5 py-3 text-[13px] text-muted transition-colors hover:border-line-strong hover:text-text disabled:opacity-50">
            <Download size={15} /> {pdfBusy ? "Preparing…" : "Download report (PDF)"}
          </button>
        </div>
      </div>
    </div>
  );
}
