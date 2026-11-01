import { motion } from "motion/react";
import { Check, X } from "lucide-react";
import DiffAddress, { closestReal } from "./DiffAddress";

const EASE = [0.16, 1, 0.3, 1];

/** One plain sentence for each way an address can imitate an organisation. */
export function reasonText(item) {
  const { brand, owner, reason, kind } = item;
  switch (reason) {
    case "BRAND_LOOKALIKE":
      return `This is spelt almost like ${brand}'s address, but it is not ${brand}'s. Letters were added, swapped or replaced so it looks right at a glance.`;
    case "BRAND_COMBOSQUAT":
      return `${brand}'s name has been joined to words like "secure", "kyc" or "update". Real ${brand} addresses are not built that way.`;
    case "BRAND_IN_DOMAIN":
      return `${brand}'s name appears inside the address, but the address belongs to ${owner}, not to ${brand}.`;
    case "BRAND_IN_SUBDOMAIN_OR_PATH":
      return `${brand}'s name is placed in front as a decoy. The real owner is ${owner}, and whoever owns it can put anything in front.`;
    case "BRAND_MISMATCH_LINK":
      return `The message talks about ${brand}, but its link goes to ${owner}, which is not one of ${brand}'s addresses.`;
    case "SENDER_LOOKALIKE":
      return `The sender's address imitates ${brand}'s. The part that matters is ${owner}, which ${brand} does not own.`;
    case "SENDER_DISPLAY_NAME_MISMATCH":
      return `The sender calls itself ${brand}, but the address it sends from belongs to ${owner}.`;
    default:
      return kind === "sender" ? `This sender's address does not belong to ${brand}.` : `This address does not belong to ${brand}.`;
  }
}

function Card({ item, index }) {
  const best = closestReal(item.official, item.shown);
  const others = item.official.filter((d) => d !== best);
  const sender = item.kind === "sender";
  return (
    <motion.article
      className="surface overflow-hidden"
      initial={{ opacity: 0, y: 22 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.8, delay: index * 0.08, ease: EASE }}
    >
      <div className="grid divide-y divide-line md:grid-cols-2 md:divide-x md:divide-y-0">
        <div className="p-6 sm:p-7">
          <p className="mb-4 flex items-center gap-2 text-[13px] font-medium text-safe"><Check size={16} /> The real {item.brand}</p>
          <p className="break-all font-mono text-[clamp(1rem,2.4vw,1.5rem)] leading-snug text-text">{best}</p>
          {others.length > 0 && <p className="mt-3 text-[12.5px] text-faint">Its other addresses: {others.join(", ")}</p>}
        </div>
        <div className="p-6 sm:p-7">
          <p className="mb-4 flex items-center gap-2 text-[13px] font-medium text-danger"><X size={16} /> {sender ? "The sender's address" : "The address in the message"}</p>
          <DiffAddress real={best} fake={item.shown} owner={item.owner} reveal />
          <p className="mt-3 text-[12.5px] text-faint">Red letters are the ones that differ from the real address. The underlined part is who owns it.</p>
        </div>
      </div>
      <div className="border-t border-line bg-ink-3/40 px-6 py-4 sm:px-7">
        <p className="text-[14.5px] leading-relaxed text-muted">{reasonText(item)}</p>
        <p className="mt-1.5 text-[13.5px] text-faint">If you really need {item.brand}, type <b className="font-medium text-text">{best}</b> yourself or use its official app.</p>
      </div>
    </motion.article>
  );
}

/** Shown after the findings. One card per organisation that an address in the message imitates. */
export default function Impersonation({ items }) {
  if (!items?.length) return null;
  return <div className="space-y-5">{items.map((it, i) => <Card key={it.brand + it.shown} item={it} index={i} />)}</div>;
}
