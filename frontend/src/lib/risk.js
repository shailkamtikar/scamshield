/**
 * Semantic styling + copy for each risk_level the backend can return.
 * risk_level is a free-text string from Gemini (see backend GeminiAssessment) —
 * anything outside these four keys falls back to the `default` entry below.
 */
export const RISK_LEVELS = {
  LOW: {
    label: "Low Risk",
    headline: "No Significant Risk Detected",
    description:
      "ScamShield's investigation did not surface meaningful phishing or scam indicators in this content.",
    text: "text-risk-low",
    edge: "border-risk-low-edge",
    bg: "bg-risk-low-bg",
    dot: "bg-risk-low",
    icon: "check_circle",
  },
  MEDIUM: {
    label: "Medium Risk",
    headline: "Some Risk Signals Found",
    description:
      "A few indicators were detected. Review the evidence below before trusting this content.",
    text: "text-risk-medium",
    edge: "border-risk-medium-edge",
    bg: "bg-risk-medium-bg",
    dot: "bg-risk-medium",
    icon: "warning",
  },
  HIGH: {
    label: "High Risk",
    headline: "High Risk Detected",
    description:
      "Multiple strong scam or phishing indicators were found. Treat this content as unsafe.",
    text: "text-risk-high",
    edge: "border-risk-high-edge",
    bg: "bg-risk-high-bg",
    dot: "bg-risk-high",
    icon: "gpp_maybe",
  },
  CRITICAL: {
    label: "Critical Risk",
    headline: "Critical Risk Detected",
    description:
      "This content shows strong evidence of a scam or phishing attempt. Do not act on it.",
    text: "text-risk-critical",
    edge: "border-risk-critical-edge",
    bg: "bg-risk-critical-bg",
    dot: "bg-risk-critical",
    icon: "gpp_bad",
  },
  default: {
    label: "Unknown",
    headline: "Assessment Returned",
    description: "ScamShield returned a risk level outside the standard set. Review the details below.",
    text: "text-text-muted",
    edge: "border-border-strong",
    bg: "bg-surface-high",
    dot: "bg-text-faint",
    icon: "help",
  },
};

export function getRiskConfig(riskLevel) {
  if (!riskLevel) return RISK_LEVELS.default;
  const key = String(riskLevel).trim().toUpperCase();
  return RISK_LEVELS[key] || RISK_LEVELS.default;
}
