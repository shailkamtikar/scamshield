import { diffAgainst } from "../lib/domains";

/**
 * An address drawn character by character against the real one.
 * `reveal` turns the highlights on: letters that are added or changed (red) and the part that tells you who owns it (underlined).
 */
export default function DiffAddress({ real, fake, owner, reveal = true }) {
  const segs = diffAgainst(real, fake);
  const ownerStart = fake.length - (owner || "").length;
  let pos = 0;
  return (
    <p className="break-all font-mono text-[clamp(1rem,2.4vw,1.5rem)] leading-snug" aria-label={fake}>
      {segs.flatMap((seg) => {
        const out = [];
        for (let k = 0; k < seg.text.length; k += 1) {
          const idx = pos + k;
          const hit = reveal && seg.kind === "diff";
          const isOwner = reveal && owner && idx >= ownerStart;
          out.push(
            <span
              key={idx}
              aria-hidden
              className={`transition-colors duration-500 ${hit ? "rounded-[3px] bg-[rgba(255,77,94,0.22)] text-danger" : isOwner ? "text-text" : "text-muted"} ${isOwner ? "underline decoration-[var(--color-danger)] decoration-2 underline-offset-[6px]" : ""}`}
            >
              {seg.text[k]}
            </span>,
          );
        }
        pos += seg.text.length;
        return out;
      })}
    </p>
  );
}

/** The listed real address that the fake one most resembles. */
export function closestReal(officials, fake) {
  let best = officials[0];
  let bestScore = -1;
  for (const o of officials) {
    const score = diffAgainst(o, fake).filter((s) => s.kind === "same").reduce((n, s) => n + s.text.length, 0);
    if (score > bestScore) { best = o; bestScore = score; }
  }
  return best;
}
