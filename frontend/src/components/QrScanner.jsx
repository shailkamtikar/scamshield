import { AnimatePresence, motion } from "motion/react";
import { Camera, CameraOff, Zap } from "lucide-react";
import QrScannerLib from "qr-scanner";
import { useCallback, useEffect, useRef, useState } from "react";

const IN_APP = /(FBAN|FBAV|Instagram|Line\/|MicroMessenger|Snapchat|LinkedInApp|Twitter|GSA\/)/i;

function describeError(err) {
  const name = err?.name || String(err);
  if (!window.isSecureContext) return "The camera only works on a secure (HTTPS) page. Open ScamShield over HTTPS, or upload a QR image instead.";
  if (IN_APP.test(navigator.userAgent)) return "This in-app browser blocks the camera. Open ScamShield in Chrome or Safari, or upload a QR image instead.";
  if (/NotAllowed|Permission/i.test(name)) return "Camera permission was denied. Allow camera access in your browser's site settings, then try again, or upload a QR image.";
  if (/NotFound|Overconstrained|No camera/i.test(name)) return "No camera was found on this device. Upload a QR image instead.";
  if (/NotReadable|Abort/i.test(name)) return "The camera is being used by another app. Close it and try again.";
  return "The camera could not be started. You can upload a QR image instead.";
}

/**
 * Live QR scanner. The code is decoded ON THIS DEVICE; only the decoded text
 * is sent to the engine, and the link inside is never opened.
 */
export default function QrScanner({ onDecoded, onUnavailable }) {
  const video = useRef(null);
  const scanner = useRef(null);
  const [state, setState] = useState("idle"); // idle | starting | active | error
  const [error, setError] = useState("");
  const [flash, setFlash] = useState({ available: false, on: false });
  const [hint, setHint] = useState(false);

  const stop = useCallback(() => {
    scanner.current?.stop();
    scanner.current?.destroy();
    scanner.current = null;
    setFlash({ available: false, on: false });
  }, []);

  const start = useCallback(async () => {
    if (!navigator.mediaDevices?.getUserMedia || !window.isSecureContext) {
      setError(describeError(new Error("insecure")));
      setState("error");
      onUnavailable?.();
      return;
    }
    setState("starting");
    setHint(false);
    try {
      const instance = new QrScannerLib(
        video.current,
        (result) => {
          const text = result?.data ?? result;
          if (!text) return;
          navigator.vibrate?.(30);
          stop();
          setState("idle");
          onDecoded(text);
        },
        { preferredCamera: "environment", returnDetailedScanResult: true, highlightScanRegion: false, highlightCodeOutline: true, maxScansPerSecond: 15 },
      );
      scanner.current = instance;
      await instance.start();
      setFlash({ available: await instance.hasFlash(), on: false });
      setState("active");
    } catch (err) {
      stop();
      setError(describeError(err));
      setState("error");
      onUnavailable?.();
    }
  }, [onDecoded, onUnavailable, stop]);

  // Camera must never keep running in the background.
  useEffect(() => {
    const onHide = () => document.hidden && scanner.current && (stop(), setState("idle"));
    document.addEventListener("visibilitychange", onHide);
    return () => {
      document.removeEventListener("visibilitychange", onHide);
      stop();
    };
  }, [stop]);

  useEffect(() => {
    if (state !== "active") return undefined;
    const id = setTimeout(() => setHint(true), 12000);
    return () => clearTimeout(id);
  }, [state]);

  return (
    <div>
      <div className="relative aspect-[4/3] w-full overflow-hidden border hairline bg-ink-3 sm:aspect-[16/10]">
        <video ref={video} playsInline muted className={`h-full w-full object-cover ${state === "active" ? "opacity-100" : "opacity-0"} transition-opacity duration-500`} />

        <AnimatePresence>
          {state === "active" && (
            <motion.div className="pointer-events-none absolute inset-0" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_35%,rgba(5,7,13,0.75)_100%)]" />
              <div className="absolute left-1/2 top-1/2 h-[58%] w-[58%] max-w-[300px] -translate-x-1/2 -translate-y-1/2" style={{ aspectRatio: "1/1" }}>
                {[["top-0 left-0", "border-l-2 border-t-2"], ["top-0 right-0", "border-r-2 border-t-2"], ["bottom-0 left-0", "border-b-2 border-l-2"], ["bottom-0 right-0", "border-b-2 border-r-2"]].map(([pos, b]) => (
                  <span key={pos} className={`absolute h-6 w-6 ${pos} ${b}`} style={{ borderColor: "rgb(var(--tint))" }} />
                ))}
                <div className="scanline absolute inset-x-0 h-10" style={{ animation: "scan-sweep 2.2s linear infinite" }} />
              </div>
              <div className="label absolute inset-x-0 bottom-3 text-center !text-text">
                {hint ? "Hold steady, fill the frame, add light" : "Point at a QR code"}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {state !== "active" && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 px-6 text-center">
            {state === "error" ? <CameraOff size={32} strokeWidth={1.3} className="text-danger" /> : <Camera size={34} strokeWidth={1.3} className="tint-text" />}
            {state === "error" ? (
              <p role="alert" className="max-w-[420px] text-[13px] leading-relaxed text-muted">{error}</p>
            ) : (
              <>
                <div className="display text-[26px]">Scan with camera</div>
                <p className="max-w-[420px] text-[13px] leading-relaxed text-muted">
                  The code is read on your device. Only its text is sent for checking, and the link is <b className="text-text">never opened</b>.
                </p>
              </>
            )}
            {state !== "error" && (
              <button type="button" onClick={start} disabled={state === "starting"} className="inline-flex items-center gap-2 border border-[rgb(var(--tint))] px-5 py-2.5 text-[13px] font-medium tint-text transition-colors hover:bg-[rgba(var(--tint),0.12)] disabled:opacity-50">
                {state === "starting" ? "Starting camera…" : "Allow camera & scan"}
              </button>
            )}
          </div>
        )}
      </div>

      {state === "active" && (
        <div className="mt-3 flex items-center justify-between">
          <button type="button" onClick={() => { stop(); setState("idle"); }} className="border hairline px-3 py-1.5 text-[12px] text-muted transition-colors hover:text-text">Stop camera</button>
          {flash.available && (
            <button
              type="button"
              onClick={async () => { await scanner.current?.toggleFlash(); setFlash((f) => ({ ...f, on: !f.on })); }}
              className={`inline-flex items-center gap-1.5 border px-3 py-1.5 text-[12px] ${flash.on ? "tint-border tint-text" : "hairline text-muted"}`}
            >
              <Zap size={13} /> Torch
            </button>
          )}
        </div>
      )}
    </div>
  );
}
