import { animate, AnimatePresence, motion, useReducedMotion } from "motion/react";
import { ArrowUpRight, Check, ChevronDown, Copy, Download, Eye, EyeOff, Phone, RotateCcw } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { MODE_CONFIG, MODES } from "../lib/modes";
import { REACH_LABEL, TRUST_LABEL, getVerdict } from "../lib/verdict";
import { ageLabel, defang, shortUrl } from "../lib/format";
import DomainBreakdown from "./DomainBreakdown";
import { ExternalLink } from "./sections/Help";

const EASE = [0.16, 1, 0.3, 1];
const reveal = (i = 0) => ({ initial: { opacity: 0, y: 24 }, whileInView: { opacity: 1, y: 0 }, viewport: { once: true, margin: "-60px" }, transition: { duration: 0.8, delay: i * 0.06, ease: EASE } });

const ACTION_LABEL = { ALLOW: "Fine to proceed", PROMOTIONAL: "Read it, ignore the ad", SPAM: "Delete it", WARN: "Verify before acting", BLOCK: "Do not engage, report it", VERIFY: "Verify independently" };

function useCount(value, duration = 1.4) {
  const reduce = useReducedMotion();
  const [n, setN] = useState(reduce ? value : 0);
  useEffect(() => {
    if (reduce) { setN(value); return undefined; }
    const c = animate(0, value, { duration, delay: 0.5, ease: EASE, onUpdate: (v) => setN(v) });
    return () => c.stop();
  }, [value, duration, reduce]);
  return n;
}

/* -------------------------------------------------------------- risk gauge */
const R = 92;
const CX = 110;
const CY = 112;
const polar = (pct) => {
  const a = Math.PI * (1 - pct / 100);
  return [CX + R * Math.cos(a), CY - R * Math.sin(a)];
};
const arc = (from, to) => {
  const [x1, y1] = polar(from);
  const [x2, y2] = polar(to);
  return `M ${x1} ${y1} A ${R} ${R} 0 0 1 ${x2} ${y2}`;
};

function Gauge({ score, color, unscored }) {
  const v = useCount(unscored ? 0 : score);
  const [mx, my] = polar(Math.max(0.5, Math.min(99.5, v)));
  return (
    <div className="relative mx-auto w-full max-w-[300px]">
      <svg viewBox="0 0 220 128" className="w-full" role="img" aria-label={unscored ? "No risk score" : `Risk ${score} out of 100`}>
        <path d={arc(0, 19.5)} stroke="var(--color-safe)" strokeOpacity="0.28" strokeWidth="10" strokeLinecap="round" fill="none" />
        <path d={arc(20.5, 59.5)} stroke="var(--color-warn)" strokeOpacity="0.28" strokeWidth="10" strokeLinecap="round" fill="none" />
        <path d={arc(60.5, 100)} stroke="var(--color-danger)" strokeOpacity="0.28" strokeWidth="10" strokeLinecap="round" fill="none" />
        {!unscored && (
          <>
            <path d={arc(0, Math.max(0.5, v))} stroke={color} strokeWidth="10" strokeLinecap="round" fill="none" />
            <circle cx={mx} cy={my} r="9" fill="var(--color-ink)" stroke={color} strokeWidth="3" />
          </>
        )}
      </svg>
      <div className="absolute inset-x-0 bottom-0 text-center">
        <div className="display text-[3.4rem] leading-none" style={{ color }}>{unscored ? "—" : Math.round(v)}</div>
        <div className="mt-1 text-[12px] text-faint">{unscored ? "no score without a link to inspect" : "out of 100"}</div>
      </div>
    </div>
  );
}

/* ----------------------------------------------------------- summary header */
function Summary({ result, meta }) {
  const v = getVerdict(result.verdict, result.assurance);
  const unscored = result.verdict === "COULD_NOT_VERIFY";
  const conf = Math.round((result.confidence ?? 0) * 100);
  const c = useCount(conf);
  const [open, setOpen] = useState(false);
  const f = result.confidence_factors || {};
  return (
    <div>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-[12.5px] text-faint">
        <span className="eyebrow">Result</span>
        <span>{MODE_CONFIG[meta.mode].label}</span><span aria-hidden>·</span><span>{(meta.latencyMs / 1000).toFixed(1)} s</span><span aria-hidden>·</span><span className="font-mono">{meta.ref}</span>
      </div>

      <div className="mt-8 grid items-end gap-10 lg:grid-cols-[1.35fr_1fr]">
        <div>
          <h2 aria-label={`Assessment: ${v.word}`} className="display text-[clamp(3.6rem,10vw,7.4rem)] leading-[0.95]" style={{ color: v.color }}>
            <span className="block overflow-hidden pb-[0.08em]">
              <motion.span className="block" initial={{ y: "108%" }} animate={{ y: 0 }} transition={{ duration: 1.1, ease: EASE }}>{v.word}</motion.span>
            </span>
          </h2>
          <motion.p className="mt-4 max-w-[560px] text-[clamp(1.1rem,2.2vw,1.45rem)] leading-snug" initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.45, duration: 0.8, ease: EASE }}>
            {v.headline} <span className="text-muted">{v.blurb}</span>
          </motion.p>
          <motion.div className="mt-6 flex flex-wrap items-center gap-2.5" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.8 }}>
            {result.category_label && <span className="rounded-full border border-[rgba(var(--tint),0.4)] bg-[rgba(var(--tint),0.08)] px-3.5 py-1.5 text-[13px] tint-text">{result.category_label}</span>}
            {result.action && <span className="rounded-full border border-line-strong px-3.5 py-1.5 text-[13px] text-muted">{ACTION_LABEL[result.action] || result.action}</span>}
          </motion.div>
        </div>

        <motion.div className="surface p-6" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5, duration: 0.9, ease: EASE }}>
          <p className="label mb-3 text-center">Risk indicator</p>
          <Gauge score={result.risk_score} color={v.color} unscored={unscored} />
          <div className="mt-6 border-t border-line pt-4">
            <div className="flex items-baseline justify-between">
              <span className="text-[13.5px] text-muted">Confidence in this result</span>
              <span className="display text-[1.8rem]">{Math.round(c)}%</span>
            </div>
            <div className="mt-2 h-1 overflow-hidden rounded-full bg-line"><motion.div className="h-full rounded-full bg-[rgb(var(--tint))]" initial={{ width: 0 }} animate={{ width: `${conf}%` }} transition={{ duration: 1.4, delay: 0.6, ease: EASE }} /></div>
            <button type="button" onClick={() => setOpen((x) => !x)} aria-expanded={open} className="mt-3 inline-flex items-center gap-1 text-[12.5px] text-faint transition-colors hover:text-text">
              How is this worked out? <ChevronDown size={13} className={`transition-transform ${open ? "rotate-180" : ""}`} />
            </button>
            <AnimatePresence initial={false}>
              {open && (
                <motion.p initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden pt-2 text-[12.5px] leading-relaxed text-muted">
                  Confidence reflects the evidence, not an AI guess: <b className="font-medium text-text">{Math.round((f.coverage ?? 0) * 100)}%</b> of the checks that apply completed, and <b className="font-medium text-text">{Math.round((f.agreement ?? 0) * 100)}%</b> of the strong evidence points the same way.
                  {f.missing_checks?.length > 0 && <> Unavailable right now: {f.missing_checks.join(", ").replaceAll("_", " ")}.</>}
                </motion.p>
              )}
            </AnimatePresence>
          </div>
        </motion.div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ blocks */
function Block({ title, kicker, children, i = 0 }) {
  return (
    <motion.section {...reveal(i)} className="mt-14">
      <div className="mb-5 flex items-baseline gap-3">
        <h3 className="display text-[1.9rem]">{title}</h3>
        {kicker && <span className="text-[13px] text-faint">{kicker}</span>}
      </div>
      {children}
    </motion.section>
  );
}

function Reasons({ result }) {
  return (
    <div className="surface divide-y divide-line">
      {result.reasons.map((r, i) => (
        <motion.div key={i} {...reveal(i)} className="grid grid-cols-[2.2rem_1fr] gap-3 p-4 sm:p-5">
          <span className="display tint-text text-[1.6rem] leading-none">{i + 1}</span>
          <p className="text-[15.5px] leading-relaxed">{r}</p>
        </motion.div>
      ))}
      <p className="px-5 py-3 text-[12px] leading-relaxed text-faint">
        {result.reasoning_model ? `Explained by ${result.reasoning_model}. ` : "Explained by built-in rules. "}The verdict and score come from fixed rules, not from the AI.
      </p>
    </div>
  );
}

const STRENGTH_COLOR = { decisive: "bg-danger", strong: "bg-danger", moderate: "bg-warn", weak: "bg-faint" };

function WarningSigns({ result }) {
  const seen = new Set();
  const signs = [];
  const add = (s) => {
    if (s.polarity !== "risk" || seen.has(s.label || s.id)) return;
    seen.add(s.label || s.id);
    signs.push(s);
  };
  (result.message_signals || []).forEach(add);
  result.urls.forEach((u) => u.signals.forEach((s) => add({ ...s, label: s.label || s.id.replaceAll("_", " ").toLowerCase() })));
  const checked = new Set();
  const good = [];
  result.urls.forEach((u) => u.signals.filter((s) => s.polarity === "trust").forEach((s) => { if (!checked.has(s.id)) { checked.add(s.id); good.push(s); } }));
  const order = { decisive: 0, strong: 1, moderate: 2, weak: 3 };
  signs.sort((a, b) => (order[a.strength] ?? 4) - (order[b.strength] ?? 4));

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <div className="surface p-5">
        <p className="label mb-4 !text-warn">Warning signs found</p>
        {signs.length === 0 ? <p className="text-[15px] text-muted">None. Nothing in the message or its links raised a concern.</p> : (
          <ul className="space-y-3.5">
            {signs.map((s) => (
              <li key={s.id + (s.target || "")} className="flex gap-3">
                <span className={`mt-[9px] h-1.5 w-1.5 shrink-0 rounded-full ${STRENGTH_COLOR[s.strength] || "bg-faint"}`} />
                <span><span className="block text-[15px] font-medium">{s.label || s.id}</span><span className="block text-[13.5px] leading-relaxed text-muted">{s.explanation}</span></span>
              </li>
            ))}
          </ul>
        )}
      </div>
      <div className="surface p-5">
        <p className="label mb-4 !text-safe">What checked out</p>
        {result.verdict !== "SAFE" && good.length > 0 && <p className="mb-3 text-[12.5px] text-faint">Not appearing on a threat list never proves a link is safe.</p>}
        {good.length === 0 ? <p className="text-[15px] text-muted">Nothing could be confirmed as genuine. Absence of problems is not proof of safety.</p> : (
          <ul className="space-y-3.5">
            {good.map((s) => (
              <li key={s.id + (s.target || "")} className="flex gap-3">
                <Check size={15} className="mt-[5px] shrink-0 text-safe" />
                <span className="text-[14.5px] leading-relaxed text-muted">{s.explanation}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

/** Quoted phrases from the wording rules and any link that was not clean. */
function SuspiciousParts({ result }) {
  const phrases = useMemo(() => {
    const out = new Set();
    (result.message_signals || []).filter((s) => s.polarity === "risk").forEach((s) => { const m = s.explanation.match(/"([^"]{3,80})"/); if (m) out.add(m[1]); });
    return [...out];
  }, [result]);
  const links = result.urls.filter((u) => u.verdict !== "SAFE");
  if (!phrases.length && !links.length) return null;
  return (
    <Block title="Suspicious phrases and links" i={1}>
      <div className="surface p-5">
        {phrases.length > 0 && (
          <div>
            <p className="label mb-3">Wording that matched a scam pattern</p>
            <div className="flex flex-wrap gap-2">{phrases.map((p) => <span key={p} className="rounded-md border border-[rgba(255,176,32,0.35)] bg-[rgba(255,176,32,0.07)] px-2.5 py-1 font-mono text-[12.5px] text-warn">“{p}”</span>)}</div>
          </div>
        )}
        {links.length > 0 && (
          <div className={phrases.length ? "mt-5 border-t border-line pt-5" : ""}>
            <p className="label mb-3">Links to be careful with (shown unclickable)</p>
            <ul className="space-y-4">{links.map((u) => (
              <li key={u.url}>
                <p className="break-all font-mono text-[12.5px] text-faint">{shortUrl(defang(u.url), 110)}</p>
                <DomainBreakdown host={u.host} registrable={u.registrable} color="var(--color-danger)" className="mt-2" />
              </li>
            ))}</ul>
          </div>
        )}
      </div>
    </Block>
  );
}

function NextSteps({ result }) {
  const risky = result.verdict !== "SAFE";
  return (
    <div className="relative overflow-hidden rounded-2xl border border-[rgba(var(--tint),0.35)] bg-[linear-gradient(130deg,rgba(var(--tint),0.1),rgba(var(--tint),0.015)_60%)] p-6 sm:p-9">
      <p className="max-w-[760px] text-[clamp(1.15rem,2.3vw,1.55rem)] font-medium leading-snug">{result.recommendation}</p>
      {risky && (
        <div className="mt-6 flex flex-wrap items-center gap-3">
          <a href="tel:1930" className="btn-primary !py-2.5 !text-[13.5px]"><Phone size={15} /> Call 1930</a>
          <ExternalLink href="https://cybercrime.gov.in" className="btn-ghost !py-2.5 !text-[13.5px]">Report at cybercrime.gov.in <ArrowUpRight size={14} /></ExternalLink>
          <span className="text-[12.5px] text-faint">The helpline is for anyone who has lost money or shared a code.</span>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------ technical details */
function Field({ k, children }) {
  return (
    <div className="bg-ink-2 px-4 py-3">
      <div className="label !text-[10px] mb-1">{k}</div>
      <div className="text-[13px] leading-snug text-text">{children}</div>
    </div>
  );
}

const providerColor = { hit: "bg-danger", clean: "bg-safe", unavailable: "bg-faint", skipped: "bg-faint" };

function SandboxView({ sandbox }) {
  if (!sandbox) return null;
  const when = sandbox.scanned_at ? new Date(sandbox.scanned_at).toLocaleDateString() : null;
  return (
    <div className="border-t border-line p-4 sm:p-5">
      <div className="label mb-1">Browser sandbox</div>
      <p className="text-[12.5px] text-muted">
        {sandbox.source === "live_scan" ? "Opened just now in an isolated browser on a security service's computer, never on your device." : `Earlier scan${when ? ` on ${when}` : ""}, opened in an isolated browser by urlscan.io.`}
      </p>
      {sandbox.screenshot && (
        <ExternalLink href={sandbox.report || sandbox.screenshot} className="mt-3 block overflow-hidden rounded-lg border border-line">
          <img src={sandbox.screenshot} alt="Picture of the page taken in the sandbox" loading="lazy" referrerPolicy="no-referrer" className="max-h-[300px] w-full bg-ink-3 object-cover object-top" onError={(e) => { e.currentTarget.parentElement.style.display = "none"; }} />
        </ExternalLink>
      )}
      {sandbox.malicious === true && <p className="mt-2 text-[13px] text-danger">The sandbox judged this page malicious{sandbox.brands?.[0] ? `, imitating ${sandbox.brands[0]}` : ""}.</p>}
    </div>
  );
}

function InspectionCard({ u, index, nested = false }) {
  const [reveal_, setReveal] = useState(false);
  const v = getVerdict(u.verdict, u.trust.tier === "UNKNOWN" ? "no_problems_found" : "verified");
  const shown = reveal_ ? u.url : defang(u.url);
  const chain = u.reachability?.chain || [];
  const r = u.reachability;
  return (
    <article className="overflow-hidden rounded-xl border border-line bg-ink-2" style={{ borderLeft: `3px solid ${v.color}` }}>
      <div className="flex flex-wrap items-start justify-between gap-3 p-4 sm:p-5">
        <div className="min-w-0 flex-1">
          <div className="label mb-1">{nested ? "Final destination" : `Link ${index + 1}`}</div>
          <p className="break-all font-mono text-[13px] text-text">{shortUrl(shown, 120)}</p>
          <DomainBreakdown host={u.host} registrable={u.registrable} color={v.color} className="mt-3" />
          <button type="button" onClick={() => setReveal((x) => !x)} className="mt-1.5 inline-flex items-center gap-1 text-[12px] text-faint transition-colors hover:text-text">
            {reveal_ ? <EyeOff size={12} /> : <Eye size={12} />} {reveal_ ? "Hide real link" : "Show real link (never click suspicious links)"}
          </button>
        </div>
        <div className="text-right">
          <div className="display text-[1.7rem] leading-none" style={{ color: v.color }}>{v.word}</div>
          {u.score != null && <div className="mt-1 font-mono text-[11px] text-faint">score {u.score}/100</div>}
        </div>
      </div>
      <div className="grid gap-px border-t border-line bg-line sm:grid-cols-2 lg:grid-cols-4">
        <Field k="Trust">{TRUST_LABEL[u.trust.tier]}{u.trust.brand && <span className="text-muted"> · {u.trust.brand}</span>}</Field>
        <Field k="Domain age">{ageLabel(u.domain_age_days) || <span className="text-faint">not available</span>}</Field>
        <Field k="Reachability">
          {r ? <>{REACH_LABEL[r.outcome] || r.outcome.replaceAll("_", " ").toLowerCase()}{r.status ? ` (${r.status})` : ""}{chain.length > 1 && <span className="text-muted"> · {chain.length - 1} redirect{chain.length > 2 ? "s" : ""}</span>}</> : <span className="text-faint">not checked</span>}
        </Field>
        <Field k="Threat lists">
          {u.reputation.length ? (
            <span className="flex flex-wrap gap-x-3 gap-y-1">
              {u.reputation.map((p) => <span key={p.provider} className="inline-flex items-center gap-1.5 text-[12px]" title={p.detail}><span className={`h-1.5 w-1.5 rounded-full ${providerColor[p.status]}`} />{p.provider.replace("Google ", "")}</span>)}
            </span>
          ) : <span className="text-faint">not checked</span>}
        </Field>
      </div>
      {u.page_title && <p className="border-t border-line px-4 py-3 text-[12.5px] text-muted sm:px-5">Page title: <span className="text-text">{u.page_title}</span></p>}
      <SandboxView sandbox={u.sandbox} />
      {u.destination && <div className="border-t border-line p-3 sm:p-4"><InspectionCard u={u.destination} index={0} nested /></div>}
    </article>
  );
}

function QrCard({ qr, decoded, codes }) {
  const [show, setShow] = useState(false);
  if (!qr) return null;
  const s = qr.summary;
  return (
    <div className="mb-5 overflow-hidden rounded-xl border border-line bg-ink-2">
      <div className="grid gap-px bg-line sm:grid-cols-3">
        <Field k="QR contains">{qr.title}</Field>
        {qr.service && <Field k="Verified service">{qr.service.name}</Field>}
        {s && (<>
          <Field k="Payee name">{s.payee || "—"}</Field>
          <Field k="Payment address (VPA)"><span className="break-all font-mono text-[12px]">{s.vpa || "—"}</span></Field>
          <Field k="Amount">{s.amount ? `₹ ${s.amount}` : "Not preset: you choose"}</Field>
          <Field k="Note">{s.note || "—"}</Field>
        </>)}
      </div>
      {s && <p className="border-t border-line p-4 text-[13px] text-muted">Scanning a payment QR sends money <b className="font-medium text-text">out</b>. You never need to scan a QR or enter your UPI PIN to <i>receive</i> money. Confirm the payee name before paying.</p>}
      <div className="border-t border-line p-4">
        <button type="button" onClick={() => setShow((x) => !x)} className="text-[12px] text-faint transition-colors hover:text-text">{show ? "Hide" : "Show"} raw QR content (text only, never opened)</button>
        {show && <pre className="mt-2 whitespace-pre-wrap break-all font-mono text-[12px] text-muted">{decoded}</pre>}
      </div>
      {codes?.length > 1 && (
        <div className="border-t border-line p-4 text-[13px]">
          <p className="mb-1.5 text-text">This picture holds {codes.length} QR codes. The result above is for the riskiest one.</p>
          <ul className="space-y-1 text-muted">{codes.map((c, i) => <li key={i} className="break-all">{getVerdict(c.verdict, "no_problems_found").word}: {shortUrl(defang(c.decoded_text), 70)}</li>)}</ul>
        </div>
      )}
    </div>
  );
}

function Evidence({ result }) {
  const [open, setOpen] = useState(false);
  const rows = result.score_breakdown || [];
  return (
    <div>
      <div className="mb-4 divide-y divide-line rounded-xl border border-line bg-ink-2">
        {rows.length === 0 && <p className="p-4 text-[14px] text-muted">No risk or trust signals were produced.</p>}
        {rows.map((r) => (
          <div key={r.signal} className="flex items-center justify-between gap-4 px-4 py-3 text-[14px]">
            <span>{r.signal}</span>
            <span className={`font-mono text-[12px] ${r.points > 0 ? "text-danger" : "text-safe"}`}>{r.points > 0 ? "+" : ""}{r.points}</span>
          </div>
        ))}
      </div>
      <button type="button" onClick={() => setOpen((x) => !x)} aria-expanded={open} className="inline-flex items-center gap-1.5 text-[12.5px] text-muted transition-colors hover:text-text">
        <ChevronDown size={13} className={`transition-transform ${open ? "rotate-180" : ""}`} /> Full technical trail ({result.evidence.length})
      </button>
      <AnimatePresence initial={false}>
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
    <div className="mb-5 grid gap-px overflow-hidden rounded-xl border border-line bg-line sm:grid-cols-3">
      {groups.map(([k, label]) => <Field key={k} k={`${label} found`}><span className="break-all font-mono text-[12px]">{entities[k].join(", ")}</span></Field>)}
    </div>
  );
}

function EmailCard({ email }) {
  if (!email) return null;
  const a = email.authentication || {};
  return (
    <div className="mb-5 overflow-hidden rounded-xl border border-line bg-ink-2">
      <div className="grid gap-px bg-line sm:grid-cols-2 lg:grid-cols-4">
        <Field k="From">{email.from_name ? `${email.from_name} ` : ""}<span className="break-all font-mono text-[12px]">{email.from || "—"}</span></Field>
        <Field k="Replies go to"><span className="break-all font-mono text-[12px]">{email.reply_to || "same as sender"}</span></Field>
        <Field k="Authentication">{["spf", "dkim", "dmarc"].filter((k) => a[k]).map((k) => `${k.toUpperCase()} ${a[k]}`).join(" · ") || <span className="text-faint">not in the pasted headers</span>}</Field>
        <Field k="Attachments">{email.attachments?.length ? email.attachments.map((x) => x.name).join(", ") : <span className="text-faint">none</span>}</Field>
      </div>
      {email.hidden_links?.length > 0 && <p className="border-t border-line p-4 text-[13px] text-warn">{email.hidden_links.length} link(s) show one address but go to another.</p>}
      <p className="border-t border-line p-4 text-[12px] text-faint">{email.note}</p>
    </div>
  );
}

function TechnicalDetails({ result, meta, imageUrl }) {
  const [open, setOpen] = useState(false);
  const showText = meta.mode === MODES.IMAGE && result.extracted_text;
  return (
    <section className="mt-14 border-t border-line pt-8">
      <button type="button" onClick={() => setOpen((x) => !x)} aria-expanded={open} className="group flex w-full items-center justify-between gap-4 text-left">
        <span>
          <span className="display block text-[1.9rem]">Technical details</span>
          <span className="text-[14px] text-muted">Link inspections, evidence trail{result.email ? ", sender and headers" : ""} and what we read. For when you want the detail.</span>
        </span>
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-line-strong text-muted transition-colors group-hover:text-text"><ChevronDown size={18} className={`transition-transform duration-300 ${open ? "rotate-180" : ""}`} /></span>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.5, ease: EASE }} className="overflow-hidden">
            <div className="space-y-10 pt-8">
              <EmailCard email={result.email} />
              {(result.urls.length > 0 || result.qr) && (
                <div>
                  <p className="label mb-4">{result.urls.length > 1 ? "Link inspections" : result.qr ? "What the QR does" : "Link inspection"}</p>
                  <QrCard qr={result.qr} decoded={result.decoded_text} codes={result.qr_codes} />
                  {!result.qr && <Entities entities={result.entities} />}
                  <div className="space-y-4">{result.urls.map((u, i) => <InspectionCard key={u.url} u={u} index={i} />)}</div>
                  {result.skipped_urls?.length > 0 && <p className="mt-3 text-[12px] text-faint">{result.skipped_urls.length} more link(s) were not analysed (limit 6 per check).</p>}
                </div>
              )}
              {!result.urls.length && !result.qr && <div><Entities entities={result.entities} /><p className="text-[14.5px] text-muted">There were no links, so the assessment is based on the wording alone.</p></div>}
              {(showText || meta.mode === MODES.TEXT) && (
                <div>
                  <p className="label mb-4">{showText ? "Text we read from the image" : "Your message"}</p>
                  <div className="flex flex-col gap-5 sm:flex-row">
                    {imageUrl && <img src={imageUrl} alt="Uploaded screenshot" className="h-40 w-40 shrink-0 rounded-lg border border-line bg-ink-3 object-contain" />}
                    <div className="min-w-0 flex-1">
                      <p className="whitespace-pre-wrap break-words font-mono text-[13px] leading-relaxed text-muted">{showText ? result.extracted_text : meta.input.message}</p>
                      {result.extraction && <p className="mt-3 font-mono text-[11px] text-faint">Read by {result.extraction.method.replace("+", " + ")}{result.extraction.sender ? ` · sender: ${result.extraction.sender}` : ""}</p>}
                    </div>
                  </div>
                </div>
              )}
              <div><p className="label mb-4">Evidence</p><Evidence result={result} /></div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}

/* ------------------------------------------------------------------ result */
export default function Result({ meta, imageUrl, onReset }) {
  const { result } = meta;
  const [copied, setCopied] = useState(false);
  const [pdfBusy, setPdfBusy] = useState(false);
  const v = getVerdict(result.verdict, result.assurance);
  const top = useRef(null);
  useEffect(() => { window.scrollTo({ top: 0 }); }, []);

  const summary = () =>
    [`ScamShield: ${v.word.toUpperCase()}${result.verdict === "COULD_NOT_VERIFY" ? "" : ` (risk ${result.risk_score}/100, ${Math.round(result.confidence * 100)}% confidence)`}`, "", ...result.reasons.map((r) => `- ${r}`), "", `What to do: ${result.recommendation}`].join("\n");

  const copy = async () => {
    try { await navigator.clipboard.writeText(summary()); setCopied(true); setTimeout(() => setCopied(false), 2000); } catch { /* clipboard unavailable */ }
  };
  const pdf = async () => {
    setPdfBusy(true);
    try { const { generateReportPdf } = await import("../lib/pdf"); generateReportPdf(meta); } finally { setPdfBusy(false); }
  };

  return (
    <div ref={top} className="mx-auto max-w-[1040px] px-5 pb-24 pt-[112px] sm:px-8 sm:pt-[128px]">
      <Summary result={result} meta={meta} />

      <Block title="Why we say this" i={0}><Reasons result={result} /></Block>
      <Block title="What we found" i={1}><WarningSigns result={result} /></Block>
      <SuspiciousParts result={result} />
      <Block title="What to do next" i={2}><NextSteps result={result} /></Block>

      <TechnicalDetails result={result} meta={meta} imageUrl={imageUrl} />

      <div className="mt-14 flex flex-col gap-3 border-t border-line pt-8 sm:flex-row sm:items-center sm:justify-between">
        <button type="button" onClick={onReset} className="btn-primary group"><RotateCcw size={15} className="transition-transform group-hover:-rotate-90" /> Check something else</button>
        <div className="flex flex-col gap-3 sm:flex-row">
          <button type="button" onClick={copy} className="btn-ghost">{copied ? <Check size={15} /> : <Copy size={15} />} {copied ? "Copied" : "Copy summary"}</button>
          <button type="button" onClick={pdf} disabled={pdfBusy} className="btn-ghost disabled:opacity-50"><Download size={15} /> {pdfBusy ? "Preparing…" : "Download report (PDF)"}</button>
        </div>
      </div>
    </div>
  );
}
