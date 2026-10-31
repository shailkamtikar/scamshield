import { AnimatePresence, motion } from "motion/react";
import { useEffect, useMemo, useState } from "react";
import AmbientBackground from "./components/AmbientBackground";
import AnalyzeForm from "./components/AnalyzeForm";
import ChatWidget from "./components/ChatWidget";
import Hero from "./components/Hero";
import Result from "./components/Result";
import ScanTimeline from "./components/ScanTimeline";
import { Footer, Header, Rail } from "./components/Shell";
import { useInvestigation } from "./hooks/useInvestigation";
import { fetchHealth } from "./lib/api";
import { MODES } from "./lib/modes";

const PILLARS = [
  ["01", "Links", "Follows redirects and shortened links, checks Google Safe Browsing, VirusTotal, URLhaus and OpenPhish, reads domain age."],
  ["02", "Wording", "Spots urgency, threats, OTP requests, fake KYC and digital-arrest scripts in English, Hindi and Hinglish."],
  ["03", "Payments", "Reads UPI and QR codes, shows who you would pay, and flags fake refund and collect-money tricks."],
];

function Pillars() {
  return (
    <motion.div className="mt-16 grid border-y hairline sm:grid-cols-3" initial={{ opacity: 0 }} whileInView={{ opacity: 1 }} viewport={{ once: true }} transition={{ duration: 1 }}>
      {PILLARS.map(([no, title, text], i) => (
        <div key={no} className={`px-1 py-7 sm:px-6 ${i > 0 ? "border-t hairline sm:border-l sm:border-t-0" : ""}`}>
          <div className="font-mono text-[12px] tint-text">{no}</div>
          <div className="display mt-2 text-[28px]">{title}</div>
          <p className="mt-2 text-[13.5px] leading-relaxed text-muted">{text}</p>
        </div>
      ))}
    </motion.div>
  );
}

export default function App() {
  const inv = useInvestigation();
  const [mode, setMode] = useState(MODES.TEXT);
  const [health, setHealth] = useState(undefined); // undefined = checking, null = offline
  const [imageUrl, setImageUrl] = useState(null);
  const [online, setOnline] = useState(() => navigator.onLine);
  useEffect(() => {
    const on = () => setOnline(true);
    const off = () => setOnline(false);
    window.addEventListener("online", on);
    window.addEventListener("offline", off);
    return () => {
      window.removeEventListener("online", on);
      window.removeEventListener("offline", off);
    };
  }, []);

  useEffect(() => {
    let live = true;
    const ping = () => fetchHealth().then((h) => live && setHealth(h));
    ping();
    const id = setInterval(ping, 60000);
    return () => { live = false; clearInterval(id); };
  }, []);

  const verdict = inv.phase === "result" ? inv.meta?.result.verdict : inv.phase === "scanning" ? inv.preview?.verdict : undefined;
  useEffect(() => {
    if (verdict) document.documentElement.dataset.verdict = verdict;
    else delete document.documentElement.dataset.verdict;
  }, [verdict]);

  const submit = (m, input) => {
    setImageUrl((old) => { if (old) URL.revokeObjectURL(old); return input.file && m === MODES.IMAGE ? URL.createObjectURL(input.file) : null; });
    inv.run(m, input);
  };

  const reset = () => { setImageUrl((old) => { if (old) URL.revokeObjectURL(old); return null; }); inv.reset(); window.scrollTo({ top: 0, behavior: "smooth" }); };
  const done = useMemo(() => inv.stages.filter((s) => s.status === "done").length, [inv.stages]);

  return (
    <div className="relative min-h-screen">
      <AmbientBackground />
      <Header health={health} onHome={reset} />
      <Rail health={health} mode={mode} phase={inv.phase} stagesDone={done} stagesTotal={5} />

      {!online && <div role="status" className="fixed inset-x-0 top-14 z-30 bg-[color:var(--color-warn)] px-4 py-1.5 text-center text-[13px] font-medium text-ink">You are offline. ScamShield needs the internet to check things.</div>}
      <main className="mx-auto max-w-[1320px] px-4 pb-24 pt-20 sm:px-6 lg:pl-[168px]">
        <AnimatePresence mode="wait">
          {inv.phase === "idle" && (
            <motion.div key="idle" exit={{ opacity: 0, y: -16, transition: { duration: 0.3 } }}>
              <Hero />
              <div className="mt-10 max-w-[860px] sm:mt-14">
                <AnalyzeForm mode={mode} onMode={setMode} onSubmit={submit} />
              </div>
              <Pillars />
            </motion.div>
          )}

          {inv.phase === "scanning" && (
            <ScanTimeline key="scan" mode={inv.meta?.mode || mode} stages={inv.stages} partialUrls={inv.partialUrls} onCancel={inv.cancel} />
          )}

          {inv.phase === "result" && inv.meta && (
            <motion.div key="result" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5 }}>
              <Result meta={inv.meta} imageUrl={imageUrl} onReset={reset} />
            </motion.div>
          )}

          {inv.phase === "error" && (
            <motion.div key="error" role="alert" className="max-w-[720px] pt-12" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
              <div className="label mb-3 text-danger">Could not complete the check</div>
              <h2 className="display text-[clamp(2.4rem,7vw,5rem)]">Something stopped us.</h2>
              <p className="mt-4 text-[16px] leading-relaxed text-muted">{inv.error}</p>
              <button type="button" onClick={reset} className="mt-8 border border-[rgb(var(--tint))] px-6 py-3 text-[13px] font-semibold uppercase tracking-[0.12em] tint-text transition-colors hover:bg-[rgb(var(--tint))] hover:text-ink">Try again</button>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
      {health?.providers?.chat && <ChatWidget result={inv.phase === "result" ? inv.meta?.result : null} />}
      <Footer />
    </div>
  );
}
