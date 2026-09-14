/**
 * Purely cosmetic categorization of the backend's own evidence[] strings.
 *
 * Every label/icon here is derived from substrings that the backend nodes
 * themselves already produce (see backend/app/graph/nodes/*.py) — nothing
 * here invents new security facts (no ASN, SPF/DKIM, entropy, etc). If a
 * string doesn't match a known pattern it just falls back to a generic
 * "Investigation Note" card so unrecognized evidence still renders safely.
 */
export function classifyEvidence(text) {
  const lower = text.toLowerCase();

  if (lower.startsWith("social engineering indicator")) {
    const match = text.match(/indicator:\s*([a-z\s]+)\s*\(/i);
    const category = match ? match[1].trim() : "social engineering";
    return {
      badge: category.toUpperCase(),
      icon: "priority_high",
      tone: "warn",
    };
  }

  if (lower.includes("possible impersonation of")) {
    return { badge: "POSSIBLE IMPERSONATION", icon: "spellcheck", tone: "danger" };
  }

  if (lower.includes("domain matches the claimed organization")) {
    return { badge: "DOMAIN MATCH", icon: "verified", tone: "positive" };
  }

  if (lower.includes("does not closely match")) {
    return { badge: "IDENTITY MISMATCH", icon: "public_off", tone: "warn" };
  }

  if (lower.includes("does not use https")) {
    return { badge: "NO HTTPS", icon: "lock_open", tone: "warn" };
  }

  if (lower.includes("suspicious keyword")) {
    return { badge: "URL KEYWORD SIGNAL", icon: "link", tone: "warn" };
  }

  if (lower.includes("ip address instead of a domain")) {
    return { badge: "RAW IP URL", icon: "dns", tone: "danger" };
  }

  if (lower.includes("unusually large number of subdomains")) {
    return { badge: "SUBDOMAIN ANOMALY", icon: "account_tree", tone: "warn" };
  }

  if (lower.startsWith("screenshot ocr text")) {
    return { badge: "SCREENSHOT OCR", icon: "image_search", tone: "neutral" };
  }

  return { badge: "INVESTIGATION NOTE", icon: "fact_check", tone: "neutral" };
}

export const EVIDENCE_TONE_CLASSES = {
  danger: "text-risk-critical",
  warn: "text-risk-medium",
  positive: "text-risk-low",
  neutral: "text-text-muted",
};
