import { useRef, useState } from "react";

const ACCEPTED_TYPES = ["image/png", "image/jpeg", "image/jpg", "image/webp"];

export default function ImageDropzone({ file, onFileSelect, onRemove, title, subtitle, icon }) {
  const [dragActive, setDragActive] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);
  const inputRef = useRef(null);

  function selectFile(selected) {
    if (!selected) return;
    if (!ACCEPTED_TYPES.includes(selected.type)) return;
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(URL.createObjectURL(selected));
    onFileSelect(selected);
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragActive(false);
    selectFile(e.dataTransfer.files?.[0]);
  }

  function handleRemove() {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    if (inputRef.current) inputRef.current.value = "";
    onRemove();
  }

  if (file && previewUrl) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-xl border border-border bg-surface-inset p-4">
        <img
          src={previewUrl}
          alt="Upload preview"
          className="max-h-64 w-auto rounded-lg border border-border object-contain"
        />
        <div className="flex w-full items-center justify-between gap-2">
          <span className="truncate text-[12.5px] text-text-muted">{file.name}</span>
          <button
            type="button"
            onClick={handleRemove}
            className="inline-flex shrink-0 items-center gap-1 rounded-lg px-2.5 py-1.5 text-[12.5px] font-medium text-risk-critical hover:bg-risk-critical-bg"
          >
            <span className="material-symbols-outlined text-[16px]">delete</span>
            Remove
          </button>
        </div>
      </div>
    );
  }

  return (
    <label
      onDragOver={(e) => {
        e.preventDefault();
        setDragActive(true);
      }}
      onDragLeave={() => setDragActive(false)}
      onDrop={handleDrop}
      className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed p-8 text-center transition-colors ${
        dragActive
          ? "border-accent bg-accent/5"
          : "border-border bg-surface-inset hover:border-border-strong"
      }`}
    >
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-surface-high text-accent">
        <span className="material-symbols-outlined text-[24px]">{icon}</span>
      </span>
      <span className="text-[14px] font-medium text-text">{title}</span>
      <span className="text-[12.5px] text-text-muted">{subtitle}</span>
      <span className="mt-1 text-[12px] text-text-faint">PNG, JPEG, or WEBP · up to 8 MB</span>
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_TYPES.join(",")}
        onChange={(e) => selectFile(e.target.files?.[0])}
        className="hidden"
      />
    </label>
  );
}
