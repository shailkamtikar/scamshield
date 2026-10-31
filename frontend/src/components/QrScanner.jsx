import { AnimatePresence, motion } from "motion/react";
import { Camera, CameraOff, Flashlight } from "lucide-react";
import QrScannerLib from "qr-scanner";
import { useCallback, useEffect, useRef, useState } from "react";

const IN_APP = /(FBAN|FBAV|Instagram|Line\/|MicroMessenger|Snapchat|LinkedInApp|Twitter|GSA\/)/i;

function describeError(err) {
  const name = err?.name || String(err);
  if (!window.isSecureContext) return "The camera only works on a secure (https) page. You can upload a picture of the QR code instead.";
  if (IN_APP.test(navigator.userAgent)) return "This app's built-in browser blocks the camera. Open ScamShield in Chrome or Safari, or upload a picture of the QR code.";
  if (/NotAllowed|Permission/i.test(name)) return "Camera permission was turned off. Allow the camera for this site in your browser settings, or upload a picture of the QR code.";
  if (/NotFound|Overconstrained|No camera/i.test(name)) return "We couldn't find a camera on this device. You can upload a picture of the QR code instead.";
  if (/NotReadable|Abort/i.test(name)) return "Another app is using the camera. Close it and try again.";
  return "The camera couldn't start. You can upload a picture of the QR code instead.";
}

/**
 * Live QR scanner. The code is decoded ON THIS DEVICE; only its text is sent
 * for checking, and the link inside is never opened.
 */
export default function QrScanner({ onDecoded }) {
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
    }
  }, [onDecoded, stop]);

  // The camera must never keep running in the background.
  useEffect(() => {
    const onHide = () => {
      if (document.hidden && scanner.current) {
        stop();
        setState("idle");
      }
    };
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
      <div className="relative aspect-[4/3] w-full overflow-hidden rounded-xl border border-line bg-sunken sm:aspect-[16/10]">
        <video ref={video} playsInline muted className={`h-full w-full object-cover transition-opacity duration-500 ${state === "active" ? "opacity-100" : "opacity-0"}`} />

        <AnimatePresence>
          {state === "active" && (
            <motion.div className="pointer-events-none absolute inset-0" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div className="absolute left-1/2 top-1/2 h-[60%] -translate-x-1/2 -translate-y-1/2 overflow-hidden rounded-2xl border-2 border-white/90 shadow-[0_0_0_2000px_rgba(0,0,0,0.35)]" style={{ aspectRatio: "1/1" }}>
                <div className="absolute inset-x-0 h-1/6 bg-gradient-to-b from-transparent via-white/40 to-transparent" style={{ animation: "sweep 2.4s ease-in-out infinite" }} />
              </div>
              <p className="absolute inset-x-0 bottom-3 text-center text-[14px] font-medium text-white">
                {hint ? "Hold steady, and make sure the code is well lit" : "Point your camera at the QR code"}
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {state !== "active" && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 px-6 text-center">
            <span className={`mb-1 flex h-12 w-12 items-center justify-center rounded-full ${state === "error" ? "bg-[color:var(--unknown-soft)] text-soft" : "bg-brand-soft text-brand"}`}>
              {state === "error" ? <CameraOff size={22} /> : <Camera size={23} />}
            </span>
            {state === "error" ? (
              <p role="alert" className="max-w-[430px] text-[15px] text-soft">{error}</p>
            ) : (
              <>
                <p className="font-medium">Scan with your camera</p>
                <p className="max-w-[430px] text-[14px] text-soft">The code is read on your device, and the link inside is never opened on your phone.</p>
                <button type="button" onClick={start} disabled={state === "starting"} className="btn-primary mt-3 !py-2.5">
                  {state === "starting" ? "Starting the camera…" : "Turn on camera"}
                </button>
              </>
            )}
          </div>
        )}
      </div>

      {state === "active" && (
        <div className="mt-3 flex items-center justify-between">
          <button type="button" onClick={() => { stop(); setState("idle"); }} className="btn-quiet !px-3 !py-1.5 !text-[14px]">Stop camera</button>
          {flash.available && (
            <button
              type="button"
              onClick={async () => { await scanner.current?.toggleFlash(); setFlash((f) => ({ ...f, on: !f.on })); }}
              className="btn-quiet !px-3 !py-1.5 !text-[14px]"
              aria-pressed={flash.on}
            >
              <Flashlight size={15} /> {flash.on ? "Torch off" : "Torch on"}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
