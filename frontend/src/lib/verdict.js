export const VERDICTS = {
  SAFE: {
    word: "Safe",
    color: "var(--color-safe)",
    headline: "No threats found.",
    blurb: "Every check came back clean for what you submitted.",
    icon: "check",
  },
  SUSPICIOUS: {
    word: "Suspicious",
    color: "var(--color-warn)",
    headline: "Don't trust this yet.",
    blurb: "Some warning signs showed up. Verify through an official channel before acting.",
    icon: "alert",
  },
  DANGEROUS: {
    word: "Dangerous",
    color: "var(--color-danger)",
    headline: "Do not open or reply.",
    blurb: "Strong evidence of a scam or phishing attempt.",
    icon: "x",
  },
  COULD_NOT_VERIFY: {
    word: "Unverified",
    color: "var(--color-unknown)",
    headline: "We couldn't verify this.",
    blurb: "The link doesn't exist or can't be reached, so there was nothing to inspect.",
    icon: "help",
  },
};

export const getVerdict = (v) => VERDICTS[v] || VERDICTS.COULD_NOT_VERIFY;

export const TRUST_LABEL = {
  OFFICIAL: "Verified official",
  POPULAR: "Well-known site",
  UNKNOWN: "Not on any trusted list",
};
