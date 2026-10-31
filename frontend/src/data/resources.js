/**
 * Resource library. Every link here is an official or well-known public site and was reachable when added.
 * To extend the library, add an item to a group (or a new group); the Help section renders whatever is here.
 */
export const HELPLINE = { number: "1930", label: "National Cyber Crime Helpline", note: "Call at once if money has left your account. The first hours matter most." };

export const RESOURCE_GROUPS = [
  {
    id: "report",
    title: "Report it",
    blurb: "Reporting helps stop the same scam reaching the next person.",
    items: [
      { title: "National Cyber Crime Reporting Portal", note: "File a complaint for any online fraud or cybercrime.", href: "https://cybercrime.gov.in", org: "Government of India" },
      { title: "Report a phishing page", note: "Tell Google about a fake website so it can be blocked in browsers.", href: "https://safebrowsing.google.com/safebrowsing/report_phish/", org: "Google Safe Browsing" },
      { title: "Sanchar Saathi", note: "Report suspected fraud calls and messages and manage mobile connections in your name.", href: "https://sancharsaathi.gov.in", org: "Department of Telecommunications" },
      { title: "CERT-In", note: "India's national agency for cyber security incidents and advisories.", href: "https://www.cert-in.org.in", org: "Government of India" },
    ],
  },
  {
    id: "check",
    title: "Check a website",
    blurb: "Second opinions on a link, from independent services.",
    items: [
      { title: "Google Safe Browsing site status", note: "See whether Google currently flags a website as unsafe.", href: "https://transparencyreport.google.com/safe-browsing/search", org: "Google" },
      { title: "VirusTotal", note: "Scan a link with dozens of security engines at once.", href: "https://www.virustotal.com", org: "VirusTotal" },
      { title: "urlscan.io", note: "See what a page looks like and where it leads, without visiting it.", href: "https://urlscan.io", org: "urlscan.io" },
    ],
  },
  {
    id: "learn",
    title: "Stay safe",
    blurb: "Short, official guides on banking safety and identity protection.",
    items: [
      { title: "RBI Kehta Hai", note: "The Reserve Bank's public awareness campaign on safe banking and frauds.", href: "https://rbikehtahai.rbi.org.in", org: "Reserve Bank of India" },
      { title: "RBI financial literacy", note: "Guides on safe digital banking, cards and UPI.", href: "https://www.rbi.org.in/Scripts/FinancialLiteracy.aspx", org: "Reserve Bank of India" },
      { title: "Lock your Aadhaar biometrics", note: "Protect your identity from misuse through the official myAadhaar portal.", href: "https://myaadhaar.uidai.gov.in", org: "UIDAI" },
    ],
  },
];

export const AFTER_A_SCAM = [
  { n: "1", title: "Call 1930", text: "Report it on the helpline straight away. Quick reports give the best chance of freezing the money." },
  { n: "2", title: "Tell your bank", text: "Use the number on the back of your card or the official app. Ask them to block cards, UPI and net banking." },
  { n: "3", title: "File a report", text: "Lodge a complaint at cybercrime.gov.in and keep the screenshots, numbers and transaction references." },
  { n: "4", title: "Change your passwords", text: "Change passwords and PINs for anything you shared, starting with banking and email." },
];
