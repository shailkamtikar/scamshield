import { AnimatePresence, motion } from "motion/react";
import { Link2, MessageCircleWarning, QrCode } from "lucide-react";
import { useEffect, useState } from "react";
import AnalyzeForm from "./components/AnalyzeForm";
import Result from "./components/Result";
import ScanTimeline from "./components/ScanTimeline";
import { Footer, Header } from "./components/Shell";
import { useInvestigation } from "./hooks/useInvestigation";
import { fetchHealth } from "./lib/api";
import { MODES } from "./lib/modes";

const EASE = [0.22, 1, 0.36, 1];

const HOW = [
  [Link2, "We look at where a link really goes", "We follow it safely, check it against security lists, and see how old the site is and what the page asks for."],
  [MessageCircleWarning, "We read the message like an expert", "We spot pressure, threats, OTP requests and fake KYC notices, in English, Hindi and Hinglish."],
  [QrCode, "We tell you what a QR code will do", "See who a UPI code pays and where a link leads, without opening anything on your phone."],
];

function Intro() {
  return (
    <div className="mx-auto max-w-[640px] pt-8 text-center sm:pt-14">
      <motion.h1 className="text-[36px] sm:text-[48px]" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, ease: EASE }}>
        Not sure about a message?
      </motion.h1>
      <motion.p className="mt-3 text-[17px] leading-relaxed text-soft sm:text-[19px]" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.1, ease: EASE }}>
        Check a message, screenshot or QR code before you tap anything. It's free and takes a few seconds.
      </motion.p>
    </div>
  );
}

function HowItWorks() {
  return (
    <div className="mx-auto mt-12 grid max-w-[880px] gap-6 sm:grid-cols-3">
      {HOW.map(([Icon, title, text], i) => (
        <motion.div key={title} initial={{ opacity: 0, y: 14 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.6, delay: i * 0.08, ease: EASE }}>
          <span className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-soft text-brand"><Icon size={20} /></span>
          <h2 className="mt-3 text-[19px]">{title}</h2>
          <p className="mt-1 text-[15px] leading-relaxed text-soft">{text}</p>
        </motion.div>
      ))}
    </div>
  );
}

export default function App() {
  const inv = useInvestigation();
  const [mode, setMode] = useState(MODES.TEXT);
  const [health, setHealth] = useState(undefined); // undefined = checking, null = unreachable
  const [imageUrl, setImageUrl] = useState(null);
  const [online, setOnline] = useState(() => navigator.onLine);

  useEffect(() => {
    let live = true;
    const ping = () => fetchHealth().then((h) => live && setHealth(h));
    ping();
    const id = setInterval(ping, 60000);
    return () => {
      live = false;
      clearInterval(id);
    };
  }, []);

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

  const submit = (m, input) => {
    setImageUrl((old) => {
      if (old) URL.revokeObjectURL(old);
      return input.file && m === MODES.IMAGE ? URL.createObjectURL(input.file) : null;
    });
    inv.run(m, input);
  };

  const reset = () => {
    setImageUrl((old) => {
      if (old) URL.revokeObjectURL(old);
      return null;
    });
    inv.reset();
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="flex min-h-screen flex-col">
      <Header health={health} onHome={reset} />
      {!online && <div role="status" className="bg-[color:var(--warn-soft)] px-4 py-2 text-center text-[15px]">You're offline. ScamShield needs the internet to check things.</div>}

      <main className="mx-auto w-full max-w-[880px] flex-1 px-4 pb-14 sm:px-6">
        <AnimatePresence mode="wait">
          {inv.phase === "idle" && (
            <motion.div key="idle" exit={{ opacity: 0, y: -10, transition: { duration: 0.2 } }}>
              <Intro />
              <div className="mx-auto mt-8 max-w-[680px]">
                <AnalyzeForm mode={mode} onMode={setMode} onSubmit={submit} />
              </div>
              <HowItWorks />
            </motion.div>
          )}

          {inv.phase === "scanning" && <ScanTimeline key="scan" stages={inv.stages} onCancel={inv.cancel} />}

          {inv.phase === "result" && inv.meta && (
            <motion.div key="result" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, transition: { duration: 0.2 } }} transition={{ duration: 0.4 }}>
              <Result meta={inv.meta} imageUrl={imageUrl} onReset={reset} />
            </motion.div>
          )}

          {inv.phase === "error" && (
            <motion.div key="error" role="alert" className="mx-auto max-w-[560px] pt-14 text-center" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }}>
              <h2 className="text-[30px]">We couldn't finish this check</h2>
              <p className="mt-3 text-[17px] leading-relaxed text-soft">{inv.error}</p>
              <button type="button" onClick={reset} className="btn-primary mt-6">Try again</button>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
      <Footer />
    </div>
  );
}
