import { splitHost } from "../lib/domains";

/** An address with its owner picked out: everything before the owner can be typed by anyone. */
export default function DomainBreakdown({ host, registrable, color = "var(--color-text)", className = "" }) {
  const { sub, owner } = splitHost(host, registrable);
  return (
    <div className={className}>
      <p className="break-all font-mono text-[14px]">
        {sub && <span className="text-faint">{sub}.</span>}
        <span className="rounded-[4px] px-1 font-semibold" style={{ color, background: `color-mix(in srgb, ${color} 14%, transparent)`, boxShadow: `inset 0 -2px 0 ${color}` }}>{owner}</span>
      </p>
      <p className="mt-1.5 text-[12px] text-faint">
        {sub ? <>The owner of this address is <b className="font-medium text-muted">{owner}</b>. Anything in front of it ({sub}) can be added by whoever owns it.</> : <>The owner of this address is <b className="font-medium text-muted">{owner}</b>.</>}
      </p>
    </div>
  );
}
