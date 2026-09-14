import { useEffect, useRef, useState } from "react";
import Header from "./components/Header";
import Footer from "./components/Footer";
import AnalyzeForm from "./components/AnalyzeForm";
import LoadingPanel from "./components/LoadingPanel";
import ResultPanel from "./components/ResultPanel";
import ErrorPanel from "./components/ErrorPanel";
import { investigateText, investigateImage, investigateQr, checkBackendHealth } from "./lib/api";
import { MODES } from "./lib/modes";

function makeLocalRef() {
  const time = Date.now().toString(36).toUpperCase();
  const rand = Math.random().toString(36).slice(2, 6).toUpperCase();
  return `LOCAL-${time}-${rand}`;
}

const INVESTIGATORS = {
  [MODES.TEXT]: investigateText,
  [MODES.SMS_IMAGE]: investigateImage,
  [MODES.QR_CODE]: investigateQr,
};

// idle -> loading -> result | error
export default function App() {
  const [status, setStatus] = useState("idle");
  const [mode, setMode] = useState(MODES.TEXT);
  const [submission, setSubmission] = useState(null);
  const [result, setResult] = useState(null);
  const [latencyMs, setLatencyMs] = useState(null);
  const [localRef, setLocalRef] = useState(null);
  const [generatedAt, setGeneratedAt] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [backendOnline, setBackendOnline] = useState(null);
  const imagePreviewUrlRef = useRef(null);
  const [imagePreviewUrl, setImagePreviewUrl] = useState(null);

  useEffect(() => {
    checkBackendHealth().then(setBackendOnline);
  }, []);

  useEffect(() => {
    return () => {
      if (imagePreviewUrlRef.current) URL.revokeObjectURL(imagePreviewUrlRef.current);
    };
  }, []);

  async function handleSubmit(formValues) {
    setSubmission(formValues);
    setStatus("loading");
    setErrorMessage("");

    if (imagePreviewUrlRef.current) {
      URL.revokeObjectURL(imagePreviewUrlRef.current);
      imagePreviewUrlRef.current = null;
    }
    if (formValues.file) {
      const url = URL.createObjectURL(formValues.file);
      imagePreviewUrlRef.current = url;
      setImagePreviewUrl(url);
    } else {
      setImagePreviewUrl(null);
    }

    try {
      const investigate = INVESTIGATORS[formValues.mode];
      const { result: data, latencyMs: ms } = await investigate(formValues);
      setResult(data);
      setLatencyMs(ms);
      setLocalRef(makeLocalRef());
      setGeneratedAt(new Date());
      setStatus("result");
      setBackendOnline(true);
    } catch (err) {
      setErrorMessage(err.message || "An unexpected error occurred.");
      setStatus("error");
      if (err.status === undefined) setBackendOnline(false);
    }
  }

  function handleReset() {
    setStatus("idle");
    setResult(null);
    setSubmission(null);
    setErrorMessage("");
    if (imagePreviewUrlRef.current) {
      URL.revokeObjectURL(imagePreviewUrlRef.current);
      imagePreviewUrlRef.current = null;
    }
    setImagePreviewUrl(null);
  }

  return (
    <div className="flex min-h-screen flex-col bg-bg">
      <Header backendOnline={backendOnline} />

      <main className="mx-auto w-full max-w-[860px] flex-1 px-4 pb-16 pt-24 md:px-8">
        {status === "idle" && (
          <div className="flex flex-col gap-6">
            <div className="text-center">
              <h1 className="font-display text-[1.75rem] font-semibold tracking-tight text-text md:text-[2rem]">
                Investigate a suspicious message
              </h1>
              <p className="mx-auto mt-2 max-w-[520px] text-[14px] text-text-muted">
                ScamShield runs your content through URL, impersonation, and social-engineering
                checks, then a Gemini-powered risk assessment — in one request.
              </p>
            </div>
            <AnalyzeForm mode={mode} onModeChange={setMode} onSubmit={handleSubmit} disabled={false} />
          </div>
        )}

        {status === "loading" && <LoadingPanel mode={mode} />}

        {status === "result" && result && (
          <ResultPanel
            result={result}
            submission={submission}
            mode={mode}
            imagePreviewUrl={imagePreviewUrl}
            latencyMs={latencyMs}
            localRef={localRef}
            generatedAt={generatedAt}
            onReset={handleReset}
          />
        )}

        {status === "error" && <ErrorPanel message={errorMessage} onRetry={handleReset} />}
      </main>

      <Footer />
    </div>
  );
}
