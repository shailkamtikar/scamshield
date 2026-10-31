const BASE = {
  SAFE: { word: "Safe", color: "var(--color-safe)", headline: "No threats found.", blurb: "We recognise this as genuine, and every check came back clean." },
  SAFE_UNKNOWN: { word: "Clear", color: "var(--color-safe)", headline: "No problems found.", blurb: "Nothing we checked raised a concern, but we don't know this site well, so stay a little careful." },
  SAFE_PAYMENT: { word: "Valid", color: "var(--color-safe)", headline: "A proper payment request.", blurb: "Nothing suspicious in it. We can't confirm who owns the account, so check the payee name before you pay." },
  SAFE_NO_LINKS: { word: "Clear", color: "var(--color-safe)", headline: "No warning signs.", blurb: "The wording doesn't look like a scam, and there are no links to check." },
  PROMO: { word: "Promotion", color: "var(--color-promo)", headline: "An advertisement.", blurb: "Reading it is harmless, and its link goes to the organisation's own site. Offers can still expire, so check details in the official app." },
  PROMO_UNVERIFIED: { word: "Promotion", color: "var(--color-promo)", headline: "An advertisement.", blurb: "Reading it is harmless, but we couldn't confirm where its link leads. Don't tap it; open the official app or site yourself." },
  SUSPICIOUS: { word: "Suspicious", color: "var(--color-warn)", headline: "Don't trust this yet.", blurb: "Some warning signs showed up. Verify through an official channel before acting." },
  DANGEROUS: { word: "Dangerous", color: "var(--color-danger)", headline: "Do not open or reply.", blurb: "Strong evidence of a scam or phishing attempt." },
  COULD_NOT_VERIFY: { word: "Unverified", color: "var(--color-unknown)", headline: "We couldn't verify this.", blurb: "The link doesn't exist or can't be reached, so there was nothing to inspect." },
};

export const VERDICTS = BASE;

/** `assurance` separates "we know this is genuine" from "we found no problems". */
export function getVerdict(verdict, assurance) {
  if (verdict === "SAFE") {
    if (assurance === "verified") return BASE.SAFE;
    if (assurance === "valid_payment") return BASE.SAFE_PAYMENT;
    if (assurance === "no_links") return BASE.SAFE_NO_LINKS;
    if (assurance === "promotion") return BASE.PROMO;
    if (assurance === "promotion_unverified") return BASE.PROMO_UNVERIFIED;
    return assurance ? BASE.SAFE_UNKNOWN : BASE.SAFE;
  }
  return BASE[verdict] || BASE.COULD_NOT_VERIFY;
}

export const TRUST_LABEL = {
  OFFICIAL: "Verified official",
  POPULAR: "Well-known site",
  UNKNOWN: "Not on any trusted list",
};

export const REACH_LABEL = {
  OK: "opens normally",
  NXDOMAIN: "address does not exist",
  NOT_FOUND: "page not found",
  TIMEOUT: "did not respond in time",
  CONNECT_FAILED: "could not connect",
  TLS_ERROR: "security certificate problem",
  SERVER_ERROR: "server error",
  LOOP: "redirects in circles",
  TOO_MANY_HOPS: "too many redirects",
  BLOCKED: "blocked for safety",
  ERROR: "could not check",
};
