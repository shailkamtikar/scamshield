import { AnimatePresence, motion } from "motion/react";
import { ImageUp, X } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { validateImage } from "../lib/validators";

export default function Dropzone({ file, onFile, title, subtitle }) {
  const input = useRef(null);
  const [over, setOver] = useState(false);
  const [error, setError] = useState("");
  const preview = useMemo(() => (file ? URL.createObjectURL(file) : null), [file]);

  useEffect(() => () => preview && URL.revokeObjectURL(preview), [preview]);

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
        className={`relative flex min-h-[210px] items-center justify-center overflow-hidden rounded-xl border-2 border-dashed transition-colors duration-200 ${
          over ? "border-brand bg-brand-soft" : "border-line-strong hover:border-brand"
        } ${file ? "cursor-default" : "cursor-pointer"}`}
      >
        <input ref={input} type="file" accept="image/png,image/jpeg,image/webp" className="hidden" onChange={(e) => accept(e.target.files?.[0])} aria-label="Choose an image" />
        <AnimatePresence mode="wait">
          {file && preview ? (
            <motion.div key="preview" className="flex w-full flex-col items-center gap-4 p-5 sm:flex-row" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <div className="h-[150px] w-[150px] shrink-0 overflow-hidden rounded-lg border border-line bg-sunken">
                <img src={preview} alt="Your upload" className="h-full w-full object-contain" />
              </div>
              <div className="min-w-0 text-center sm:text-left">
                <p className="truncate font-medium">{file.name}</p>
                <p className="text-[14px] text-soft">{Math.max(1, Math.round(file.size / 1024))} KB, ready to check</p>
                <button type="button" onClick={(e) => { e.stopPropagation(); onFile(null); setError(""); }} className="btn-quiet mt-3 !px-3 !py-1.5 !text-[14px]">
                  <X size={15} /> Remove
                </button>
              </div>
            </motion.div>
          ) : (
            <motion.div key="empty" className="flex flex-col items-center gap-1.5 px-6 py-4 text-center" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <motion.span animate={over ? { y: -4 } : { y: 0 }} transition={{ type: "spring", stiffness: 300, damping: 18 }} className="mb-1 flex h-12 w-12 items-center justify-center rounded-full bg-brand-soft text-brand">
                <ImageUp size={23} />
              </motion.span>
              <p className="font-medium">{title}</p>
              <p className="text-[14px] text-soft">{subtitle}</p>
              <p className="text-[13px] text-faint">PNG, JPEG or WEBP, up to 8 MB. You can also paste an image.</p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
      {error && <p role="alert" className="mt-2 text-[14px] text-[color:var(--danger)]">{error}</p>}
    </div>
  );
}
