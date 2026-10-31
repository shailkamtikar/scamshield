/** Make a link unclickable by default: https://a.com -> hxxps://a[.]com */
export function defang(url = "") {
  return url.replace(/^http/i, "hxxp").replace(/\./g, "[.]");
}

export function shortUrl(url = "", max = 56) {
  const clean = url.replace(/^https?:\/\//i, "");
  return clean.length > max ? `${clean.slice(0, max - 1)}…` : clean;
}

export function ageLabel(days) {
  if (days == null) return null;
  if (days < 1) return "registered today";
  if (days < 60) return `${days} days old`;
  if (days < 730) return `${Math.round(days / 30)} months old`;
  return `${Math.floor(days / 365)} years old`;
}
