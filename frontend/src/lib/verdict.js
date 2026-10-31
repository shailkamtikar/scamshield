/** Plain-language wording. `assurance` separates "we know this site" from "we found nothing". */
const VERDICTS = {
  SAFE_VERIFIED: {
    title: "This looks safe",
    blurb: "We recognise this as genuine, and nothing we checked raised a concern.",
    badge: "Looks safe",
  },
  SAFE_UNKNOWN: {
    title: "We found no problems",
    blurb: "Nothing we checked raised a concern, but we don't know this site well, so stay a little careful.",
    badge: "No problems found",
  },
  SAFE_PAYMENT: {
    title: "This is a valid payment request",
    blurb: "The QR code is a proper UPI request with nothing suspicious in it. We can't confirm who owns the account, so check the name before you pay.",
    badge: "Valid payment QR",
  },
  SAFE_NO_LINKS: {
    title: "We found no warning signs",
    blurb: "Nothing in the wording looks like a scam, and there are no links to check.",
    badge: "No warning signs",
  },
  SUSPICIOUS: {
    title: "Be careful with this",
    blurb: "Some warning signs showed up. Check with the organisation directly before you do anything.",
    badge: "Be careful",
  },
  DANGEROUS: {
    title: "This looks like a scam",
    blurb: "We found strong signs of a scam or phishing attempt. Please don't open the link or reply.",
    badge: "Likely scam",
  },
  COULD_NOT_VERIFY: {
    title: "We couldn't check this link",
    blurb: "The link doesn't exist or didn't respond, so there was nothing for us to inspect.",
    badge: "Couldn't check",
  },
};

export function getVerdict(verdict, assurance) {
  if (verdict === "SAFE") {
    if (assurance === "verified") return VERDICTS.SAFE_VERIFIED;
    if (assurance === "valid_payment") return VERDICTS.SAFE_PAYMENT;
    if (assurance === "no_links") return VERDICTS.SAFE_NO_LINKS;
    return VERDICTS.SAFE_UNKNOWN;
  }
  return VERDICTS[verdict] || VERDICTS.COULD_NOT_VERIFY;
}

export function confidenceWord(c) {
  if (c >= 0.9) return "Very sure";
  if (c >= 0.75) return "Fairly sure";
  if (c >= 0.55) return "Somewhat sure";
  return "Not very sure";
}

export const TRUST_LABEL = {
  OFFICIAL: "Verified official site",
  POPULAR: "Well-known website",
  UNKNOWN: "Not a site we recognise",
};

export const REACH_LABEL = {
  OK: "Opens normally",
  NXDOMAIN: "This address doesn't exist",
  NOT_FOUND: "Page not found",
  TIMEOUT: "Didn't respond in time",
  CONNECT_FAILED: "Couldn't connect",
  TLS_ERROR: "Security certificate problem",
  SERVER_ERROR: "The site has a server error",
  LOOP: "Redirects in circles",
  TOO_MANY_HOPS: "Too many redirects",
  BLOCKED: "Blocked for safety",
  ERROR: "Couldn't check",
};
