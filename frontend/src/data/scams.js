/**
 * Educational content. Every message below is an ILLUSTRATIVE example written for this page.
 * None of them is a detected threat, a real sender or a real campaign.
 */

export const CATEGORIES = [
  {
    id: "phishing",
    name: "Phishing messages",
    short: "Pose as a trusted brand to steal logins and codes.",
    detail: "A message copies the tone and logo of a bank, a government office or a shop and pushes you to a page that looks the same. Anything you type there goes to the scammer.",
    flags: ["A link that is not the organisation's own address", "A login or card form reached from a message", "Pressure to act within hours"],
    sample: "Your Netflix payment failed. Update billing at netfIix-billing.top within 24 hours or your account closes.",
  },
  {
    id: "delivery",
    name: "Fake delivery notices",
    short: "A small \"redelivery fee\" that hides a card grab.",
    detail: "You get a text about a parcel you may or may not be waiting for. The page asks for a tiny fee, but it is collecting your card details and one-time codes.",
    flags: ["A parcel you did not order", "A fee for redelivery or customs", "A link on a random domain"],
    sample: "India Post: parcel held, address incomplete. Pay Rs 25 redelivery fee at dc9x35ez.top/pay today.",
  },
  {
    id: "banking",
    name: "Banking and KYC scams",
    short: "\"Your account will be blocked\" unless you update KYC.",
    detail: "Real banks do ask for KYC updates, but through the app, the branch or their own website. Scam versions threaten to freeze your account and send you to a fake page or a mobile number.",
    flags: ["A threat to block or freeze the account", "A link or number that is not the bank's own", "A request for OTP, PIN or card details"],
    sample: "Dear customer, your SBI account will be blocked today. Update KYC now: sbi-kyc-update.top or call 98xxxxxx10.",
  },
  {
    id: "investment",
    name: "Investment scams",
    short: "Guaranteed returns, VIP groups and tips.",
    detail: "You are added to a chat group where \"members\" post huge profits. A fake trading app shows gains, until you try to withdraw.",
    flags: ["Guaranteed or fixed high returns", "A private Telegram or WhatsApp group", "Pressure to deposit before a deadline"],
    sample: "Join our VIP stock tips group. 300% returns assured this month, limited seats. t.me/sureshotipo",
  },
  {
    id: "job",
    name: "Job offer scams",
    short: "Easy pay for simple tasks, then a fee to \"unlock\" it.",
    detail: "A recruiter offers well paid work for liking videos or rating products. Early payouts are small and real; then the tasks ask you to deposit money that never comes back.",
    flags: ["Pay far above the work involved", "Contact only through WhatsApp or Telegram", "A fee or deposit before you can earn"],
    sample: "Part-time job: earn Rs 5,000 a day rating products. Message HR on WhatsApp to start today.",
  },
  {
    id: "impersonation",
    name: "Impersonation scams",
    short: "Police, officials, family or support staff who are not.",
    detail: "The caller claims to be from the CBI, customs, your bank or even your child on a new number, and says you are in trouble or someone is. The aim is to rush you into paying or sharing a code.",
    flags: ["An unexpected official or relative", "A threat of arrest or an emergency", "A demand to pay or stay on the line"],
    sample: "This is Cyber Cell. A parcel in your name has illegal items. Stay on this video call and transfer funds to a safe account.",
  },
  {
    id: "url",
    name: "Suspicious URLs",
    short: "Look-alike domains and links that hide where they go.",
    detail: "Scammers register names that look right at a glance, swap letters, add words like secure or kyc, or hide the real address behind a shortener.",
    flags: ["Letters swapped for look-alikes (rn for m, I for l)", "A real brand name inside an unrelated domain", "A shortened link with no preview"],
    sample: "hdfcbank.secure-kyc-login.com/verify, which sits on secure-kyc-login.com, not hdfcbank.com",
  },
  {
    id: "qr",
    name: "QR-code scams",
    short: "A code that pays out instead of paying in.",
    detail: "You are told to scan a code to receive a refund or prize. Scanning a payment QR always sends money, and a pasted sticker can cover the real one.",
    flags: ["Scan to receive money", "A code pasted over another", "A payee name that does not match who you expect"],
    sample: "Your refund of Rs 4,999 is ready. Scan this QR with any UPI app and enter your PIN to receive it.",
  },
  {
    id: "support",
    name: "Fake customer support",
    short: "Numbers found in search results and pop-ups.",
    detail: "A search or a pop-up gives a \"helpline\" that belongs to a scammer, who asks you to install a remote-access app or share a code to fix your problem.",
    flags: ["A support number from a pop-up or an ad", "A request to install remote-access software", "Asks for a code sent to your phone"],
    sample: "Your computer is infected with 5 viruses. Call the Microsoft technician now and allow remote access.",
  },
];

/** Phrases are marked with [[id|text]]; the page highlights them when the matching sign is selected. */
export const SIGNS = [
  { id: "urgent", title: "Urgent requests for action", text: "Deadlines like \"today\" or \"within 2 hours\" are meant to stop you thinking. Real organisations give notice and offer official routes.", tip: "Slow down. Open the official app yourself." },
  { id: "short", title: "Suspicious shortened URLs", text: "Shorteners hide the real destination. A bank or government office does not need one for an urgent warning.", tip: "Check where it goes before you tap, or don't tap at all." },
  { id: "otp", title: "Requests for OTPs or passwords", text: "An OTP, PIN or password is for you alone. No bank, courier or officer needs it from you by message or call.", tip: "Never share it, whatever the reason." },
  { id: "pay", title: "Unexpected payment requests", text: "Small fees, \"refund\" collect requests and processing charges are how scams collect money, or your card.", tip: "You never need to pay to receive money." },
  { id: "who", title: "Impersonating legitimate organisations", text: "Names, logos and tone are easy to copy. The address, number and sender are what you can check.", tip: "Compare the link with the organisation's real website." },
  { id: "good", title: "Too-good-to-be-true offers", text: "Prizes you did not enter for, guaranteed returns and big pay for easy work are bait.", tip: "If it sounds unreal, it probably is." },
];

export const SIGN_MESSAGE = [
  { t: "SBI Rewards: " },
  { t: "Your account will be blocked today.", s: "urgent" },
  { t: " Verify KYC at " },
  { t: "bit.ly/sbi-kyc-9x", s: "short" },
  { t: " and " },
  { t: "share the OTP", s: "otp" },
  { t: " to avoid penalty. You have also won " },
  { t: "Rs 5,000 cashback", s: "good" },
  { t: ", " },
  { t: "pay Rs 49 fee to claim", s: "pay" },
  { t: ". From the " },
  { t: "State Bank Security Team", s: "who" },
  { t: "." },
];

export const EXAMPLES = [
  {
    id: "parcel",
    title: "Fake parcel delivery SMS",
    kind: "Delivery",
    message: "India Post: your parcel could not be delivered due to an incomplete address. Pay Rs 25 redelivery fee: https://dc9x35ez.top/pay",
    org: "",
    flags: [
      ["A parcel you may not be expecting", "Scammers send these to thousands of numbers hoping some people are waiting for something."],
      ["A small fee to pay", "The amount is tiny so you don't hesitate. The page is built to capture your card details and OTP."],
      ["https://dc9x35ez.top", "A random string on a .top domain. India Post uses indiapost.gov.in. Government domains end in .gov.in."],
    ],
  },
  {
    id: "kyc",
    title: "Fake bank KYC update",
    kind: "Banking",
    message: "Dear customer, your SBI account will be blocked today. Update KYC immediately: http://sbi-kyc-update.top/login or call 9876543210",
    org: "SBI",
    flags: [
      ["\"Will be blocked today\"", "Real banks do not freeze accounts with a few hours' notice by SMS."],
      ["sbi-kyc-update.top", "The bank's name inside someone else's domain. SBI's real sites end in sbi.co.in, onlinesbi.sbi or sbi.bank.in."],
      ["A mobile number to call", "Banks use toll-free numbers printed on your card. A mobile number is a person pretending to be the bank."],
    ],
  },
  {
    id: "job",
    title: "Fraudulent job offer",
    kind: "Job",
    message: "Hello, you are shortlisted for a part-time role at Flipkart. Earn Rs 5,000 daily by rating products. Message HR Neha on WhatsApp 9123456780 to start today.",
    org: "",
    flags: [
      ["Daily pay for rating products", "Real jobs don't pay this for a few minutes of simple work. The early payouts are bait."],
      ["Contact only on WhatsApp", "Genuine recruiters use company email addresses and official career pages."],
      ["Names a big brand", "Using Flipkart's name borrows trust. Check the company's careers site directly."],
    ],
  },
  {
    id: "invest",
    title: "Fake investment opportunity",
    kind: "Investment",
    message: "Join our exclusive stock tips group. 300% returns assured in one month. Sure-shot IPO allotment tips. Link: https://t.me/sureshotipo",
    org: "",
    flags: [
      ["\"300% returns assured\"", "No legitimate investment can guarantee returns, let alone these."],
      ["A private Telegram group", "Scams use groups where fake members post profits to create pressure."],
      ["IPO allotment \"tips\"", "Allotment is by lottery. Nobody can guarantee it."],
    ],
  },
];
