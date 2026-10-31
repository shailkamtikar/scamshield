import { AnimatePresence, motion } from "motion/react";
import { ImageUp, X } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

const MAX_BYTES = 8 * 1024 * 1024;
const TYPES = ["image/png", "image/jpeg", "image/webp"];

export function validateImage(file) {
  if (!TYPES.includes(file.type)) return "Please use a PNG, JPEG or WEBP image.";
  if (file.size > MAX_BYTES) return "That image is larger than 8 MB.";
  return null;
}

export default function Dropzone({ file, onFile, title, subtitle }) {
  const input = useRef(null);
  const [over, setOver] = useState(false);
  const [error, setError] = useState("");
  const [preview, setPreview] = useState(null);

  useEffect(() => {
    if (!file) {
      setPreview(null);
      return undefined;
    }
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const accept = useCallback(
    (f) => {
      if (!f) return;
      const problem = validateImage(f);
      setError(problem || "");
      if (!problem) onFile(f);
    },
    [onFile],
  );

  useEffect(() => {
    const onPaste = (e) => {
      const item = [...(e.clipboardData?.items || [])].find((i) => i.type.startsWith("image/"));
      if (item) accept(item.getAsFile());
    };
    window.addEventListener("paste", onPaste);
    return () => window.removeEventListener("paste", onPaste);
  }, [accept]);

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        aria-label={title}
        onClick={() => !file && input.current?.click()}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && !file && input.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setOver(true); }}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => { e.preventDefault(); setOver(false); accept(e.dataTransfer.files?.[0]); }}
        className={`relative flex min-h-[230px] items-center justify-center overflow-hidden border border-dashed transition-colors duration-300 ${
          over ? "tint-border tint-bg" : "border-line-strong hover:border-[rgba(var(--tint),0.5)]"
        } ${file ? "cursor-default" : "cursor-pointer"}`}
      >
        <input ref={input} type="file" accept={TYPES.join(",")} className="hidden" onChange={(e) => accept(e.target.files?.[0])} />
        <AnimatePresence mode="wait">
          {file && preview ? (
            <motion.div key="preview" className="relative flex w-full items-center gap-5 p-5" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div className="relative h-[170px] w-[170px] shrink-0 overflow-hidden border hairline bg-ink-3">
                <img src={preview} alt="Selected upload" className="h-full w-full object-contain" />
                <div className="scanline absolute inset-x-0 h-12" style={{ animation: "scan-sweep 2.6s linear infinite" }} />
              </div>
              <div className="min-w-0">
                <div className="label mb-1">Ready to scan</div>
                <div className="truncate text-[14px] text-text">{file.name}</div>
                <div className="font-mono text-[11px] text-faint">{(file.size / 1024).toFixed(0)} KB</div>
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); onFile(null); setError(""); }}
                  className="mt-4 inline-flex items-center gap-1.5 border hairline px-3 py-1.5 text-[12px] text-muted transition-colors hover:border-line-strong hover:text-text"
                >
                  <X size={13} /> Remove
                </button>
              </div>
            </motion.div>
          ) : (
            <motion.div key="empty" className="flex flex-col items-center gap-3 px-6 text-center" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <motion.div animate={over ? { y: -6, scale: 1.08 } : { y: 0, scale: 1 }} transition={{ type: "spring", stiffness: 300, damping: 18 }}>
                <ImageUp size={34} strokeWidth={1.3} className="tint-text" />
              </motion.div>
              <div className="display text-[26px] tracking-wide">{title}</div>
              <div className="text-[13px] text-muted">{subtitle}</div>
              <div className="label !text-[10px]">PNG · JPEG · WEBP · max 8 MB · or paste with Ctrl+V</div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
      {error && <p role="alert" className="mt-2 text-[13px] text-danger">{error}</p>}
    </div>
  );
}
