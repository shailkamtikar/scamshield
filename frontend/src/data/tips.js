/** Safety tips. Static on purpose: this page must work with no backend and no connection. */
export const RULES = [
  { n: "1", title: "Never share an OTP, PIN or password", text: "Not with a caller, an \"officer\", a courier or a bank employee. Real organisations never ask for these." },
  { n: "2", title: "Pause before you act", text: "Scams run on hurry. A real notice survives a 30-second pause and a call to the official number." },
  { n: "3", title: "Open the official app yourself", text: "Don't use the link in the message. Type the address or open the app you already have." },
  { n: "4", title: "You never pay to receive money", text: "Scanning a QR or entering your UPI PIN only ever sends money out." },
  { n: "5", title: "Read the address from the right", text: "The owner is the last name before the ending. Whatever sits in front can be added by anyone." },
  { n: "6", title: "Unknown number, big promise, small fee: stop", text: "Prizes, refunds, easy jobs and guaranteed returns that cost you a small fee first are the same trick." },
];

export const CHECKLIST = [
  "Did I expect this message, and does it come from the number or address I normally see?",
  "Does it rush me or threaten me (blocked, arrested, last chance)?",
  "Does it ask for a code, a PIN, a password or card details?",
  "Is the link's owner the real organisation, not just a name inside a longer address?",
  "Would the organisation really ask this by message, not through its app or a branch?",
  "Can I check it by calling the number printed on my card or on the official website?",
];

export const DOS = [
  "Use the number on the back of your card or the official website to call your bank.",
  "Turn on app lock and transaction alerts for UPI and banking apps.",
  "Report scam numbers and messages, then block them.",
  "Tell family, especially older relatives, about the scams below.",
  "Keep screenshots, numbers and transaction IDs if something goes wrong.",
];

export const DONTS = [
  "Don't install apps from a link or an APK file someone sends you.",
  "Don't allow screen sharing or remote access (AnyDesk, TeamViewer) for \"support\".",
  "Don't scan a QR code to receive a refund or a prize.",
  "Don't stay on a call with someone who says you are under \"digital arrest\". It does not exist.",
  "Don't pay a \"fee\" first to unlock a loan, job, parcel or prize.",
];

export const GLOSSARY = [
  ["Digital arrest", "A call or video call from \"police, CBI or customs\" saying you are under arrest unless you pay. No agency does this. Hang up."],
  ["KYC update link", "A message saying your account will be blocked unless you update KYC through a link. Banks do KYC in the app or at a branch."],
  ["UPI collect request", "A request that looks like money is coming to you. Approving it with your PIN sends money out."],
  ["Redelivery or customs fee", "A small fee to release a parcel you may not be expecting. The page collects your card details."],
  ["Task or part-time job", "Pay for liking videos or rating products. Early payouts are real; then you are asked to deposit money that never returns."],
  ["VIP investment group", "A private group where \"members\" post huge profits. The trading app shows gains until you try to withdraw."],
];

export const NUMBERS = [
  ["1930", "National Cyber Crime Helpline. Call straight away if money has left your account."],
  ["Your bank", "Use the number printed on the back of your card to block cards, UPI and net banking."],
  ["cybercrime.gov.in", "File a complaint online once you have a connection."],
];
