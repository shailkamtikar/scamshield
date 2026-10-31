import { animate, AnimatePresence, motion, useReducedMotion } from "motion/react";
import { AlertTriangle, Check, CheckCircle2, ChevronDown, CircleHelp, Copy, Download, Eye, EyeOff, RotateCcw, ShieldAlert } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { MODES } from "../lib/modes";
import { REACH_LABEL, TRUST_LABEL, confidenceWord, getVerdict } from "../lib/verdict";
import { ageLabel, defang, shortUrl } from "../lib/format";

const EASE = [0.22, 1, 0.36, 1];
const reveal = (i = 0) => ({ initial: { opacity: 0, y: 16 }, whileInView: { opacity: 1, y: 0 }, viewport: { once: true, margin: "-40px" }, transition: { duration: 0.6, delay: i * 0.05, ease: EASE } });
const ICON = { SAFE: CheckCircle2, SUSPICIOUS: AlertTriangle, DANGEROUS: ShieldAlert, COULD_NOT_VERIFY: CircleHelp };

function CountUp({ value, duration = 1.2 }) {
  const reduce = useReducedMotion();
  const ref = useRef(null);
  useEffect(() => {
    if (reduce || !ref.current) return undefined;
    const controls = animate(0, value, {
      duration,
      ease: EASE,
      onUpdate: (v) => {
        if (ref.current) ref.current.textContent = String(Math.round(v));
      },
    });
    return () => controls.stop();
  }, [value, duration, reduce]);
  return <span ref={ref}>{value}</span>;
}

function Section({ title, children }) {
  return (
    <motion.section {...reveal()} className="mt-9">
      <h3 className="mb-3 text-[22px]">{title}</h3>
      {children}
    </motion.section>
  );
}

function Disclosure({ label, children }) {
  const [open, setOpen] = useState(false);
  return (
    <div>
      <button type="button" onClick={() => setOpen((x) => !x)} aria-expanded={open} className="inline-flex items-center gap-1 text-[14.5px] text-soft hover:text-ink">
        <ChevronDown size={16} className={`transition-transform duration-200 ${open ? "rotate-180" : ""}`} /> {label}
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.3, ease: EASE }} className="overflow-hidden">
            <div className="pt-3">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ---------------------------------------------------------------- headline */
function Summary({ result }) {
  const v = getVerdict(result.verdict, result.assurance);
  const Icon = ICON[result.verdict] || CircleHelp;
  const conf = Math.round((result.confidence ?? 0) * 100);
  const f = result.confidence_factors || {};
  const checked = result.verdict !== "COULD_NOT_VERIFY";
  return (
    <motion.div className="card overflow-hidden" initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, ease: EASE }}>
      <div className="bg-tone-soft px-5 py-6 sm:px-7 sm:py-8">
        <div className="flex items-start gap-4">
          <motion.span initial={{ scale: 0.6, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ type: "spring", stiffness: 260, damping: 18, delay: 0.1 }} className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-card text-tone">
            <Icon size={26} />
          </motion.span>
          <div className="min-w-0">
            <h2 className="text-[28px] sm:text-[34px]">{v.title}</h2>
            <p className="mt-1.5 text-[16.5px] leading-relaxed text-ink/85">{v.blurb}</p>
          </div>
        </div>
      </div>

      <div className="grid gap-5 border-t border-line p-5 sm:grid-cols-2 sm:gap-8 sm:p-7">
        <div>
          <p className="text-[14.5px] text-soft">Risk score</p>
          {checked ? (
            <>
              <p className="mt-0.5 font-serif text-[34px] font-semibold leading-tight"><CountUp value={result.risk_score} /><span className="text-[17px] font-normal text-soft"> out of 100</span></p>
              <div className="mt-2.5 h-2 overflow-hidden rounded-full bg-sunken" role="img" aria-label={`Risk ${result.risk_score} out of 100`}>
                <motion.div className="h-full rounded-full bg-tone" initial={{ width: 0 }} animate={{ width: `${Math.max(2, result.risk_score)}%` }} transition={{ duration: 1.2, delay: 0.25, ease: EASE }} />
              </div>
            </>
          ) : (
            <p className="mt-0.5 font-serif text-[22px] font-semibold leading-snug">Not scored</p>
          )}
        </div>
        <div>
          <p className="text-[14.5px] text-soft">How sure we are</p>
          <p className="mt-0.5 font-serif text-[34px] font-semibold leading-tight">{confidenceWord(result.confidence)} <span className="text-[17px] font-normal text-soft">(<CountUp value={conf} />%)</span></p>
          <div className="mt-1.5">
            <Disclosure label="How is this worked out?">
              <p className="text-[14.5px] leading-relaxed text-soft">
                This comes from the evidence, not from an AI guess: {Math.round((f.coverage ?? 0) * 100)}% of the checks that apply here finished, and {Math.round((f.agreement ?? 0) * 100)}% of the strong evidence points the same way.
                {f.missing_checks?.length > 0 && ` These checks weren't available this time: ${f.missing_checks.join(", ").replaceAll("_", " ")}.`}
              </p>
            </Disclosure>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

/* ------------------------------------------------------------------ pieces */
function NextStep({ result }) {
  return (
    <div className="rounded-xl border border-line bg-card p-5">
      <p className="text-[17px] leading-relaxed">{result.recommendation}</p>
      {result.verdict !== "SAFE" && !result.recommendation.includes("1930") && (
        <p className="mt-3 text-[15px] text-soft">If you lost money or shared a code, call <b className="font-semibold text-ink">1930</b> right away, or report it at cybercrime.gov.in.</p>
      )}
    </div>
  );
}

function Reasons({ result }) {
  return (
    <>
      <ul className="space-y-2.5">
        {result.reasons.map((r, i) => (
          <motion.li key={i} {...reveal(i)} className="flex gap-3 leading-relaxed">
            <span className="mt-[11px] h-1.5 w-1.5 shrink-0 rounded-full bg-tone" />
            <span>{r}</span>
          </motion.li>
        ))}
      </ul>
      <p className="mt-3 text-[14px] text-faint">
        {result.reasoning_model ? "Written by AI (Google Gemini) from the evidence we collected." : "Written by ScamShield's built-in rules."} The verdict and score come from fixed rules, not from the AI.
      </p>
    </>
  );
}

function Fact({ k, children }) {
  return (
    <div className="bg-card px-4 py-3">
      <dt className="text-[13.5px] text-soft">{k}</dt>
      <dd className="m-0 mt-0.5 text-[15px] leading-snug">{children}</dd>
    </div>
  );
}

const providerTone = { hit: "var(--danger)", clean: "var(--safe)", unavailable: "var(--line-strong)", skipped: "var(--line-strong)" };

function SandboxView({ sandbox }) {
  if (!sandbox) return null;
  const when = sandbox.scanned_at ? new Date(sandbox.scanned_at).toLocaleDateString() : null;
  return (
    <div className="border-t border-line p-4 sm:p-5">
      <p className="text-[14.5px] font-medium">What this page looks like</p>
      <p className="mt-0.5 text-[14px] text-soft">
        {sandbox.source === "live_scan"
          ? "Opened just now in an isolated browser on a security service's computer, not on your device."
          : `From an earlier scan${when ? ` on ${when}` : ""} in an isolated browser by urlscan.io.`}
      </p>
      {sandbox.screenshot && (
        <a href={sandbox.report || sandbox.screenshot} target="_blank" rel="noreferrer noopener" className="mt-3 block overflow-hidden rounded-lg border border-line">
          <img src={sandbox.screenshot} alt="Picture of the page taken in the sandbox" loading="lazy" referrerPolicy="no-referrer" className="max-h-[320px] w-full bg-sunken object-cover object-top" onError={(e) => { e.currentTarget.parentElement.style.display = "none"; }} />
        </a>
      )}
      {sandbox.malicious === true && <p className="mt-2 text-[14.5px] text-[color:var(--danger)]">The sandbox judged this page malicious{sandbox.brands?.[0] ? `, imitating ${sandbox.brands[0]}` : ""}.</p>}
    </div>
  );
}

function LinkCard({ u, nested = false }) {
  const [show, setShow] = useState(false);
  const v = getVerdict(u.verdict, u.trust.tier === "UNKNOWN" ? "no_problems_found" : "verified");
  const r = u.reachability;
  const redirects = Math.max(0, (r?.chain?.length || 1) - 1);
  const risk = u.signals.filter((s) => s.polarity === "risk");
  return (
    <motion.article {...(nested ? {} : reveal())} data-tone={u.verdict} className="overflow-hidden rounded-xl border border-line bg-card">
      <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2 p-4 sm:p-5">
        <div className="min-w-0 flex-1">
          {nested && <p className="mb-1 text-[14px] text-soft">Where it really goes</p>}
          <p className="break-all font-mono text-[14px]">{shortUrl(show ? u.url : defang(u.url), 110)}</p>
          <button type="button" onClick={() => setShow((x) => !x)} className="mt-1 inline-flex items-center gap-1 text-[13.5px] text-soft hover:text-ink">
            {show ? <EyeOff size={14} /> : <Eye size={14} />} {show ? "Hide the real address" : "Show the real address (please don't click it)"}
          </button>
        </div>
        <span className="rounded-full bg-tone-soft px-3 py-1 text-[14px] font-medium text-tone">{v.badge}</span>
      </div>

      <dl className="m-0 grid gap-px border-t border-line bg-line sm:grid-cols-2">
        <Fact k="Who runs it">{u.trust.brand || TRUST_LABEL[u.trust.tier]}{u.trust.brand && <span className="text-soft"> (verified)</span>}</Fact>
        <Fact k="How old the site is">{ageLabel(u.domain_age_days) || <span className="text-soft">Not known</span>}</Fact>
        <Fact k="Does it open?">
          {r ? <>{REACH_LABEL[r.outcome] || r.outcome}{redirects > 0 && <span className="text-soft">, after {redirects} redirect{redirects > 1 ? "s" : ""}</span>}</> : <span className="text-soft">Not needed for a verified site</span>}
        </Fact>
        <Fact k="Security lists">
          {u.reputation.length ? (
            <span className="flex flex-wrap gap-x-3 gap-y-1">
              {u.reputation.map((p) => (
                <span key={p.provider} className="inline-flex items-center gap-1.5 text-[14px]" title={p.detail || p.status}>
                  <span className="h-2 w-2 rounded-full" style={{ background: providerTone[p.status] }} />{p.provider.replace("Google ", "")}
                </span>
              ))}
            </span>
          ) : <span className="text-soft">Not checked</span>}
          {u.reputation.length > 0 && <span className="mt-1 block text-[13px] text-faint">Green means not listed as harmful. Grey means unavailable.</span>}
        </Fact>
      </dl>

      {risk.length > 0 && (
        <ul className="space-y-1.5 border-t border-line p-4 text-[15px] sm:p-5">
          {risk.map((s) => <li key={s.id + s.target} className="flex gap-2.5"><span className="mt-[9px] h-1.5 w-1.5 shrink-0 rounded-full bg-tone" /><span className="text-soft">{s.explanation}</span></li>)}
        </ul>
      )}
      <SandboxView sandbox={u.sandbox} />
      {u.destination && <div className="border-t border-line p-3 sm:p-4"><LinkCard u={u.destination} nested /></div>}
    </motion.article>
  );
}

function QrCard({ result }) {
  const qr = result.qr;
  if (!qr) return null;
  const s = qr.summary;
  return (
    <motion.div {...reveal()} className="mb-4 overflow-hidden rounded-xl border border-line bg-card">
      <dl className="m-0 grid gap-px bg-line sm:grid-cols-2">
        <Fact k="This QR code contains">{qr.title}</Fact>
        {qr.service && <Fact k="Verified service">{qr.service.name}</Fact>}
        {s && (
          <>
            <Fact k="Pays to">{s.payee || "No name given"}</Fact>
            <Fact k="UPI address"><span className="break-all font-mono text-[14px]">{s.vpa || "Missing"}</span></Fact>
            <Fact k="Amount">{s.amount ? `₹${s.amount}` : "You choose the amount"}</Fact>
            {s.note && <Fact k="Note">{s.note}</Fact>}
          </>
        )}
      </dl>
      {s && <p className="border-t border-line p-4 text-[15px] leading-relaxed text-soft">Scanning a payment QR sends money <b className="font-semibold text-ink">out of</b> your account. You never need to scan a QR or enter your UPI PIN to receive money. Check the name before you pay.</p>}
      <div className="border-t border-line p-4">
        <Disclosure label="Show what's inside the code (text only, not opened)">
          <pre className="m-0 whitespace-pre-wrap break-all font-mono text-[13px] text-soft">{result.decoded_text}</pre>
        </Disclosure>
      </div>
      {result.qr_codes?.length > 1 && (
        <div className="border-t border-line p-4 text-[15px]">
          <p className="mb-1 font-medium">This picture contains {result.qr_codes.length} QR codes. The result above is for the riskiest one.</p>
          <ul className="space-y-1 text-soft">
            {result.qr_codes.map((c, i) => <li key={i} className="break-all">{getVerdict(c.verdict, "no_problems_found").badge}: {shortUrl(defang(c.decoded_text), 70)}</li>)}
          </ul>
        </div>
      )}
    </motion.div>
  );
}

function Technical({ result }) {
  return (
    <Disclosure label="Technical details">
      <div className="space-y-4 rounded-xl border border-line bg-card p-4 text-[14.5px] sm:p-5">
        {result.score_breakdown?.length > 0 && (
          <table className="w-full border-collapse">
            <caption className="pb-1.5 text-left font-medium">Evidence and points</caption>
            <tbody>
              {result.score_breakdown.map((r) => (
                <tr key={r.signal} className="border-t border-line">
                  <td className="py-1.5 pr-3">{r.signal}</td>
                  <td className="py-1.5 text-right tabular-nums text-soft">{r.points > 0 ? "+" : ""}{r.points}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <div>
          <p className="mb-1.5 font-medium">Full evidence trail</p>
          <ul className="space-y-1 text-soft">{result.evidence.map((e, i) => <li key={i}>{e}</li>)}</ul>
        </div>
        <p className="text-faint">Rules applied: {result.decision_path.join(", ") || "none"}. Scoring weights version {result.weights_version}.</p>
      </div>
    </Disclosure>
  );
}

function Entities({ entities }) {
  const groups = [["phones", "Phone numbers in this message"], ["upi_ids", "UPI IDs in this message"], ["emails", "Email addresses in this message"]].filter(([k]) => entities?.[k]?.length);
  if (!groups.length) return null;
  return (
    <dl className="m-0 mb-4 grid gap-px overflow-hidden rounded-xl border border-line bg-line sm:grid-cols-2">
      {groups.map(([k, label]) => <Fact key={k} k={label}><span className="break-all font-mono text-[14px]">{entities[k].join(", ")}</span></Fact>)}
    </dl>
  );
}

/* ------------------------------------------------------------------ result */
export default function Result({ meta, imageUrl, onReset }) {
  const { result } = meta;
  const [copied, setCopied] = useState(false);
  const [pdfBusy, setPdfBusy] = useState(false);
  const v = getVerdict(result.verdict, result.assurance);
  const top = useRef(null);
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  const summary = () =>
    [`ScamShield: ${v.title}${result.verdict === "COULD_NOT_VERIFY" ? "" : ` (risk ${result.risk_score} out of 100, ${confidenceWord(result.confidence).toLowerCase()})`}`, "", ...result.reasons.map((r) => `- ${r}`), "", `What to do: ${result.recommendation}`].join("\n");

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(summary());
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard not available */
    }
  };
  const pdf = async () => {
    setPdfBusy(true);
    try {
      const { generateReportPdf } = await import("../lib/pdf");
      generateReportPdf(meta);
    } finally {
      setPdfBusy(false);
    }
  };

  const content = meta.mode === MODES.IMAGE ? result.extracted_text : meta.mode === MODES.TEXT ? meta.input.message : null;

  return (
    <div ref={top} data-tone={result.verdict} className="mx-auto max-w-[720px] pt-4 sm:pt-8">
      <Summary result={result} />

      <Section title="What you should do"><NextStep result={result} /></Section>
      <Section title="Why we think this"><Reasons result={result} /></Section>

      {(result.urls.length > 0 || result.qr) && (
        <Section title={result.qr ? "What this QR code does" : result.urls.length > 1 ? "The links we checked" : "The link we checked"}>
          <QrCard result={result} />
          <Entities entities={result.entities} />
          <div className="space-y-4">{result.urls.map((u) => <LinkCard key={u.url} u={u} />)}</div>
          {result.skipped_urls?.length > 0 && <p className="mt-3 text-[14px] text-soft">{result.skipped_urls.length} more link{result.skipped_urls.length > 1 ? "s were" : " was"} not checked (we check up to 6 at a time).</p>}
        </Section>
      )}

      {!result.urls.length && !result.qr && (
        <Section title="What we found">
          <Entities entities={result.entities} />
          <p className="text-soft">There were no links in this, so our answer is based on the wording alone.</p>
        </Section>
      )}

      {content && (
        <Section title={meta.mode === MODES.IMAGE ? "The text we read" : "Your message"}>
          <div className="flex flex-col gap-4 rounded-xl border border-line bg-card p-4 sm:flex-row sm:p-5">
            {imageUrl && <img src={imageUrl} alt="Your screenshot" className="h-36 w-36 shrink-0 rounded-lg border border-line bg-sunken object-contain" />}
            <div className="min-w-0">
              <p className="whitespace-pre-wrap break-words leading-relaxed text-soft">{content}</p>
              {result.extraction?.sender && <p className="mt-2 text-[14px] text-faint">Sender shown: {result.extraction.sender}</p>}
            </div>
          </div>
        </Section>
      )}

      <div className="mt-8"><Technical result={result} /></div>

      <div className="mt-9 flex flex-col gap-3 border-t border-line pt-6 sm:flex-row sm:items-center">
        <button type="button" onClick={onReset} className="btn-primary"><RotateCcw size={17} /> Check something else</button>
        <button type="button" onClick={copy} className="btn-quiet">{copied ? <Check size={17} /> : <Copy size={17} />} {copied ? "Copied" : "Copy summary"}</button>
        <button type="button" onClick={pdf} disabled={pdfBusy} className="btn-quiet"><Download size={17} /> {pdfBusy ? "Preparing…" : "Download report"}</button>
      </div>
    </div>
  );
}
