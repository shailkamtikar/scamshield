import { AnimatePresence, motion } from "motion/react";
import { useCallback, useEffect, useState } from "react";
import AmbientBackground from "./components/AmbientBackground";
import ChatWidget from "./components/ChatWidget";
import Footer from "./components/Footer";
import Hero from "./components/Hero";
import Nav from "./components/Nav";
import Result from "./components/Result";
import ScanTimeline from "./components/ScanTimeline";
import Examples from "./components/sections/Examples";
import Help from "./components/sections/Help";
import HowItWorks from "./components/sections/HowItWorks";
import Privacy from "./components/sections/Privacy";
import ThreatLibrary from "./components/sections/ThreatLibrary";
import { Connector } from "./components/ui/Reveal";
import WarningSigns from "./components/sections/WarningSigns";
import { useInvestigation } from "./hooks/useInvestigation";
import { fetchHealth } from "./lib/api";
import { MODES } from "./lib/modes";
import { toneOf } from "./lib/verdict";

export default function App() {
  const inv = useInvestigation();
  const [mode, setMode] = useState(MODES.TEXT);
  const [health, setHealth] = useState(undefined); // undefined = checking, null = unreachable
  const [imageUrl, setImageUrl] = useState(null);
  const [online, setOnline] = useState(() => navigator.onLine);
  const [prefill, setPrefill] = useState(null);

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

  const finished = inv.phase === "result" ? inv.meta?.result : undefined;
  const tone = toneOf(finished) || (inv.phase === "scanning" ? inv.preview?.verdict : undefined);
  useEffect(() => {
    if (tone) document.documentElement.dataset.verdict = tone;
    else delete document.documentElement.dataset.verdict;
  }, [tone]);

  const submit = (m, input) => {
    setImageUrl((old) => { if (old) URL.revokeObjectURL(old); return input.file && m === MODES.IMAGE ? URL.createObjectURL(input.file) : null; });
    inv.run(m, input);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const clearImage = () => setImageUrl((old) => { if (old) URL.revokeObjectURL(old); return null; });
  const idle = inv.phase === "idle";

  const scrollTo = (id) => {
    if (id === "top") window.scrollTo({ top: 0, behavior: "smooth" });
    else document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };
  const go = useCallback((id) => {
    if (!idle) { clearImage(); inv.reset(); setTimeout(() => scrollTo(id), 120); } else scrollTo(id);
  }, [idle, inv]); // eslint-disable-line react-hooks/exhaustive-deps

  const check = useCallback(() => {
    go("top");
    setTimeout(() => document.querySelector("textarea[aria-label='Message or link to check']")?.focus({ preventScroll: true }), 650);
  }, [go]);

  const tryExample = useCallback((ex) => {
    setMode(MODES.TEXT);
    setPrefill({ ...ex, n: Date.now() });
    go("top");
  }, [go]);

  const reset = () => { clearImage(); inv.reset(); window.scrollTo({ top: 0, behavior: "smooth" }); };

  return (
    <div className="relative min-h-screen">
      <AmbientBackground />
      <Nav onGo={go} onCheck={check} showSections={idle} />

      {!online && <div role="status" className="fixed inset-x-0 top-[68px] z-30 bg-warn px-4 py-1.5 text-center text-[13px] font-medium text-ink">You are offline. ScamShield needs the internet to check things.</div>}

      <main>
        <AnimatePresence mode="wait">
          {idle && (
            <motion.div key="idle" exit={{ opacity: 0, y: -16, transition: { duration: 0.3 } }}>
              <Hero mode={mode} onMode={setMode} onSubmit={submit} prefill={prefill} engineDown={health === null} />
              <Connector />
              <HowItWorks />
              <ThreatLibrary onTry={tryExample} />
              <WarningSigns />
              <Examples onTry={tryExample} />
              <Connector />
              <Help />
              <Privacy />
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
            <motion.div key="error" role="alert" className="mx-auto max-w-[680px] px-5 pb-24 pt-[140px] sm:px-0" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
              <span className="eyebrow !text-danger">Could not complete the check</span>
              <h2 className="display mt-4 text-[clamp(2.4rem,6vw,4rem)]">Something stopped us.</h2>
              <p className="mt-4 text-[16px] leading-relaxed text-muted">{inv.error}</p>
              <button type="button" onClick={reset} className="btn-primary mt-8">Try again</button>
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {health?.providers?.chat && <ChatWidget result={inv.phase === "result" ? inv.meta?.result : null} />}
      <Footer onGo={go} onCheck={check} />
    </div>
  );
}
