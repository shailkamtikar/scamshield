"""
Scam-language analysis for message text plus entity extraction.

Pure rules (word-boundary regexes, negation handling, Hinglish) so every
result is explainable. No network access.
"""

import re
import unicodedata
from dataclasses import dataclass, field

from app.engine.signals import Signal, make
from app.intel.registry_data import UPI_HANDLES
from app.intel.trust import GENERIC_BRAND_WORDS, brand_tokens

ZERO_WIDTH = dict.fromkeys(map(ord, "​‌‍⁠﻿­"), None)
_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "@": "a", "$": "s"})

NEGATION = re.compile(
    r"(?:never|do not|don'?t|dont|not to|should not|shouldn'?t|will not|won'?t|wont|"
    r"no one|nobody|avoid|beware|kabhi nahi|mat)\b(?:\W+\w+){0,6}?\W+$",
    re.I,
)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).translate(ZERO_WIDTH)
    return text.lower()


def _deleet_words(text: str) -> str:
    """Undo number-for-letter swaps inside words (0TP -> otp, verlfy -> verify)."""
    return re.sub(r"\b\w*[a-z]\w*\b", lambda m: m.group(0).translate(_LEET) if re.search(r"[0-9@$]", m.group(0)) and re.search(r"[a-z]", m.group(0)) else m.group(0), text)


PATTERNS: dict[str, list[str]] = {
    "URGENCY": [
        r"\burgent(?:ly)?\b", r"\bimmediately\b", r"\bact now\b", r"\bright away\b", r"\basap\b",
        r"\bwithin \d+\s*(?:hours?|hrs?|minutes?|mins?|days?)\b", r"\blast chance\b",
        r"\bexpires? (?:today|soon|tonight)\b", r"\btoday only\b", r"\bfinal (?:notice|warning|reminder)\b",
        r"\babhi\b", r"\bturant\b", r"\bjaldi\b", r"\bat once\b", r"\bwithout delay\b",
    ],
    "FEAR_OR_THREAT": [
        r"\b(?:account|a/c|acct|card|sim|number|service|services|connection|wallet|upi|id|policy|licen[cs]e|aadhaar|aadhar|pan|profile|login|access|netbanking|net banking|mobile|line|membership|subscription|kyc|fastag|gst|loan|demat|trading)\b(?:\W+\w+){0,5}?\W+(?:suspended|blocked|deactivated|terminated|disconnected|frozen|locked|restricted|banned)\b", r"\b(?:suspended|blocked|deactivated|terminated|disconnected|frozen|locked|restricted|banned)\b(?:\W+\w+){0,3}?\W+(?:your|ur|the|my|this)?\W*(?:\w+\W+){0,2}(?:account|a/c|acct|card|sim|number|service|services|connection|wallet|upi|id|policy|licen[cs]e|aadhaar|aadhar|pan|profile|login|access|netbanking|net banking|mobile|line|membership|subscription|kyc|fastag|gst|loan|demat|trading)\b",
        r"\bwill be (?:blocked|suspended|closed|disconnected|deactivated|terminated|cancelled|canceled)\b",
        r"\b(?:be|been|get|gets|getting) (?:suspended|blocked|deactivated|terminated|disconnected|frozen|locked|restricted|banned)\b",
        r"\blegal action\b", r"\bpenalt(?:y|ies)\b", r"\bfir\b", r"\bcase (?:has been )?(?:filed|registered)\b",
        r"\bband ho\s*(?:jayega|jaega|jayegi)\b", r"\bbloc?k ho\b", r"\baccount (?:closed|closure)\b",
    ],
    "ARREST_THREAT": [
        r"\barrest(?:ed)?\b", r"\bdigital arrest\b", r"\bwarrant\b", r"\b(?:cbi|narcotics|ncb|customs officer|cyber ?crime branch)\b",
        r"\bmoney laundering\b", r"\bparcel (?:contains|has been (?:seized|intercepted))\b",
        r"\b(?:police|court) (?:notice|summon|case)\b", r"\bsupreme court\b",
    ],
    "CREDENTIAL_REQUEST": [
        r"\b(?:share|send|enter|provide|confirm|give|tell|submit|reply(?: with)?|forward|update|verify|type|dictate|read out)\b"
        r"(?:\W+\w+){0,4}?\W+(?:otp|one[- ]time[- ]password|pin|upi pin|mpin|cvv|password|passcode|card number|"
        r"card details|net ?banking|verification code|login details|atm pin|expiry)\b",
        # identifiers (Aadhaar / PAN / account number): handing them over is the risk, "updating" them is just KYC wording
        r"\b(?:share|send|enter|provide|give|tell|submit|reply(?: with)?|forward|type|dictate|read out)\b"
        r"(?:\W+\w+){0,4}?\W+(?:aadhaa?r(?: number)?|pan(?: number| card)?|account number)\b",
        r"\b(?:otp|cvv|pin|password)\b\W+(?:is )?(?:required|needed|mandatory)\b",
        r"\bkindly (?:share|send|provide) .{0,20}(?:otp|pin|password|cvv)\b",
    ],
    "FINANCIAL_PRESSURE": [
        r"\brefund\b", r"\bcash ?back\b", r"\bprize\b", r"\breward points?\b", r"\bprocessing fee\b",
        r"\bclaim (?:your|the|now)\b", r"\bbonus\b", r"\bpay (?:a |the )?(?:small )?(?:fee|charges?|fine|amount)\b",
        r"\btransfer (?:the )?(?:amount|money|funds)\b", r"\bclearance (?:fee|charges?)\b", r"\bpending (?:amount|dues?|bill)\b",
        r"\b(?:rs\.?|inr|₹)\s?\d[\d,]*\b.{0,20}\b(?:credited|reward|won|prize|refund)\b",
    ],
    "PRIZE_LOTTERY": [
        r"\blotter(?:y|ies)\b", r"\blucky draw\b", r"\byou(?:'ve| have)? (?:been selected|won)\b",
        r"\bcongratulations\b.{0,60}\b(?:won|winner|selected|prize|gift)\b", r"\bkbc\b", r"\bwinner\b",
    ],
    "KYC_UPDATE": [
        r"\bkyc\b(?! (?:is |has been |was )?(?:complete|completed|done|successful|verified|approved))", r"\bre-?kyc\b", r"\bupdate (?:your )?(?:pan|aadhaa?r|account details|bank details|account|profile|mobile number|bank)\b",
        r"\b(?:pan|aadhaa?r) (?:is )?(?:not linked|expired|not updated|will be)\b", r"\bverify your (?:account|identity)\b",
        r"\bcomplete (?:your )?(?:kyc|verification)\b",
    ],
    "JOB_TASK_SCAM": [
        r"\bwork from home\b", r"\bpart[- ]?time (?:job|work)\b", r"\bearn (?:rs\.?|inr|₹)?\s?\d[\d,]*\s*(?:per|a|/)\s*(?:day|week|hour|daily)\b",
        r"\b(?:like|subscribe) (?:and )?(?:subscribe|like|share)\b", r"\bsimple tasks?\b", r"\bdata entry job\b",
        r"\bsalary (?:rs\.?|inr|₹)?\s?\d", r"\bhr (?:manager|team)\b.{0,60}\b(?:telegram|whatsapp)\b", r"\bhiring\b.{0,60}\b(?:whatsapp|telegram)\b",
        r"\bjoin (?:our )?(?:telegram|whatsapp) (?:group|channel)\b",
    ],
    "REMOTE_ACCESS_APP": [
        r"\banydesk\b", r"\bteam ?viewer\b", r"\bquick ?support\b", r"\brustdesk\b", r"\bairdroid\b", r"\bultraviewer\b",
    ],
    "APK_INSTALL": [
        r"\b\w+\.apk\b", r"\b(?:download|install) (?:the |our )?(?:\w+ )?(?:app|apk)\b(?![\s\S]{0,45}\b(?:play ?store|app ?store|google play|apple)\b)", r"\bupdate (?:the )?app from (?:this )?link\b",
    ],
    "INVESTMENT_SCAM": [
        r"\bguaranteed (?:returns?|profit)\b", r"\bdouble your (?:money|investment)\b", r"\b\d{2,3}%\s*(?:returns?|profit)\b",
        r"\b(?:vip|premium) (?:trading|stock|crypto) (?:group|tips|signals?)\b", r"\bipo allotment\b.{0,40}\b(?:group|link)\b",
        r"\bcrypto (?:trading|investment) (?:platform|group)\b", r"\binsider tips?\b",
    ],
    "UPI_COLLECT_SCAM": [
        r"\bscan (?:this |the )?(?:qr|barcode)(?: code)?\b.{0,40}\b(?:receive|get|credit|refund|claim)\b",
        r"\b(?:receive|get) (?:the )?money\b.{0,40}\b(?:scan|pin|approve|accept)\b",
        r"\bcollect request\b", r"\b(?:approve|accept) (?:the )?(?:upi |payment )?request\b.{0,40}\b(?:receive|refund|get)\b",
        r"\benter (?:your )?upi pin\b.{0,40}\b(?:receive|get|credit|refund)\b",
    ],
    "SUSPICIOUS_CTA": [
        r"\bclick (?:here|the link|below|on the link|this link)\b", r"\btap (?:here|the link|below)\b", r"\bopen (?:the |this )?link\b",
        r"\bverify now\b", r"\bconfirm now\b", r"\blogin now\b", r"\bupdate now\b", r"\bdownload (?:now|here)\b",
        r"\bvisit (?:the )?(?:link|website|site)\b", r"\bfollow (?:the )?link\b",
    ],
}


# Additional India-specific scam wording (delivery fees, utility cut-offs, loan bait).
for _sid, _extra in {
    "FEAR_OR_THREAT": [
        r"\b(?:power|electricity|connection|supply|service)\b.{0,40}\bwill be (?:cut|disconnected|stopped|blocked)\b",
        r"\b(?:power|electricity) cut\b", r"\bdisconnect(?:ion|ed)?\b",
    ],
    "FINANCIAL_PRESSURE": [
        r"\b(?:re-?delivery|delivery|customs|clearance) (?:fee|charges?)\b", r"\bheld at customs\b", r"\bpackage is held\b",
        r"\bparcel (?:could not|couldn'?t|cannot) be delivered\b", r"\bpre-?approved loan\b", r"\binstant (?:cash|loan)\b",
        r"\bwithout (?:any )?documents\b",
    ],
    "CREDENTIAL_REQUEST": [
        r"\b(?:submit|enter|share|provide|update|send)\b\W+(?:\w+\W+){0,3}(?:bank|account|card) details\b",
    ],
    "SUSPICIOUS_CTA": [
        r"\b(?:contact|call|message|msg|ping)\b.{0,30}\b(?:whatsapp|telegram)\b", r"\bwhatsapp\b\W+\+?\d",
    ],
}.items():
    PATTERNS[_sid].extend(_extra)


# Advance-fee wording, crypto bait and codes handed to a "agent" without naming the code.
for _sid, _extra in {
    "ADVANCE_FEE": [
        r"\b(?:customs|import|clearance|redelivery|re-delivery|handling) (?:duty|fee|fees|charges?|tax)\b.{0,70}\b(?:pay|upi|within|immediately|today)\b",
        r"\bpay\b.{0,40}\b(?:customs|duty)\b",
        r"\b(?:pay|deposit|transfer|send|remit)\b.{0,40}\b(?:registration|processing|insurance|joining|release|clearance|security|handling|verification|gst|tax|activation|booking)\b.{0,12}\b(?:fee|fees|charges?|deposit|amount)\b",
        r"\b(?:registration|processing|insurance|joining|release|clearance|handling|activation) (?:fee|fees|charges?)\b.{0,50}\b(?:required|first|to (?:claim|release|confirm|receive|get|join))\b",
        r"\bpay\b.{0,30}\bfee\b.{0,15}\bfirst\b",
    ],
    "CREDENTIAL_REQUEST": [
        r"\b(?:share|send|tell|give|read|forward|provide)\b\W+(?:it|this|that|the code|this code|the otp|the number)\b(?!\W+(?:only|just)\b).{0,40}\b(?:agent|executive|officer|person|caller|representative|someone|team|whatsapp|call)\b",
        r"\b(?:share|send|tell|give|read(?: out)?|forward|provide|dictate)\b(?:\W+\w+){0,4}?\W+(?:\d|six|four|5|6)[- ]?digit (?:code|otp|number|pin)\b",
        r"\b(?:share|send|tell|give|read(?: out)?|forward|provide|dictate)\b(?:\W+\w+){0,4}?\W+(?:the )?code (?:you|that you)(?: have)?(?: just)? (?:received|got|get)\b",
        r"\b(?:login|log in|sign in)\b.{0,50}\b(?:with|using)\b.{0,15}\b(?:net ?banking (?:id|password|credentials)|password|card number|pin|credentials)\b",
    ],
    "REMOTE_ACCESS_APP": [r"\ballow remote access\b", r"\bremote access\b.{0,40}\b(?:fix|repair|support|technician)\b", r"\b(?:install|download)\b.{0,30}\b(?:support|remote)\b.{0,10}\b(?:app|software|tool)\b"],
    "FEAR_OR_THREAT": [r"\binfected with \d+ viruses\b|\bviruses? (?:detected|found)\b", r"\bdo not turn off (?:the |your )?(?:computer|device|pc)\b"],
    "ARREST_THREAT": [
        r"\b(?:video|photos?|recording|pictures)\b.{0,50}\b(?:send|share|leak|post|upload)\b.{0,40}\b(?:contacts|friends|family|everyone|relatives)\b", r"\bunless you pay\b",
        r"\b(?:calling|call|message|notice|officer|inspector|this is|i am|we are)\b.{0,30}\bcyber ?(?:crime|cell)\b(?!\.)", r"\bstay on (?:the )?(?:video )?call\b", r"\b(?:safe|verification|rbi|secure) account\b.{0,40}\b(?:transfer|deposit)\b|\btransfer\b.{0,70}\b(?:safe|rbi|secure) account\b",
        r"\baadhaar\b.{0,50}\b(?:illegal|laundering|criminal|drug)\b",
    ],
    "JOB_TASK_SCAM": [
        r"\bshortlisted\b.{0,70}\b(?:part[- ]?time|work from home|role|job|position)\b", r"\brat(?:e|ing) (?:products?|hotels?|restaurants?|movies?|videos?)\b",
        r"\bpart[- ]?time (?:role|position)\b",
    ],
    "PRIZE_LOTTERY": [
        r"\b\d[\d.,]*\s*(?:million|billion)\s*(?:usd|dollars|us\$)\b", r"\bbusiness proposal\b", r"\b(?:transfer|move) (?:out of|from) (?:my )?country\b",
    ],
    "INVESTMENT_SCAM": [
        r"\bmake you rich\b|\bcrypto arbitrage\b", r"\binvest\b.{0,40}\b(?:send|get|receive|give|pay)\b.{0,30}\bback\b",
        r"\b\d{1,3}x returns?\b", r"\breturns? guaranteed\b", r"\bpre-?launch (?:coin|token|ico)\b", r"\bdeposit (?:usdt|btc|eth|crypto)\b",
        r"\bguaranteed\b.{0,30}\b(?:monthly|weekly|daily)\b.{0,15}\b(?:returns?|profit|income)\b",
    ],
    "FINANCIAL_PRESSURE": [r"\bpre-?approved\b.{0,30}\bloan\b.{0,80}\b(?:pay|fee|deposit|insurance)\b"],
}.items():
    PATTERNS.setdefault(_sid, []).extend(_extra)


# Hinglish, family-impersonation, advance-fee and "approve with PIN" tricks.
for _sid, _extra in {
    "FEAR_OR_THREAT": [
        r"\b(?:suspend|block|band|deactivate|disable)\s+hone\s+wal[ae]\b", r"\bhone wala hai\b",
    ],
    "SUSPICIOUS_CTA": [r"\bclick karke\b", r"\blink par click\b"],
    "FINANCIAL_PRESSURE": [
        r"\bthis is my new (?:number|phone|no)\b", r"\bmy phone (?:broke|is (?:broken|lost|damaged|not working))\b",
        r"\bsend (?:me )?(?:rs\.?|inr|₹)?\s?\d[\d,]*\s*(?:rupees|rs)?\s*(?:urgently|asap|now|immediately)\b",
        r"\burgently\b.{0,30}\b(?:send|transfer|pay)\b",
    ],
    "PRIZE_LOTTERY": [r"\bgift parcel\b", r"\binheritance\b", r"\bunclaimed (?:funds|fortune|prize)\b", r"\bsingapore based investor\b"],
    "UPI_COLLECT_SCAM": [
        r"\b(?:request|collect)\b.{0,50}\bpin\b.{0,30}\b(?:approve|daal|dal|enter|submit)\b",
        r"\bpin (?:daal|dal|daalo|dalo|enter)\b.{0,25}\bapprove\b",
        r"\bapprove\b.{0,25}\b(?:with|using|after entering) (?:your )?(?:upi )?pin\b",
    ],
}.items():
    PATTERNS[_sid].extend(_extra)


# Hindi in Devanagari script. \b is unreliable around Devanagari vowel signs, so these match plainly.
for _sid, _extra in {
    "URGENCY": [r"तुरंत", r"तुरन्त", r"अभी\s", r"जल्दी\s+(?:करें|करो)", r"आज\s+ही"],
    "FEAR_OR_THREAT": [r"बंद\s+(?:हो\s+जाएगा|कर\s+दिया|होने\s+वाला)", r"ब्लॉक", r"निलंबित", r"सस्पेंड", r"रद्द\s+(?:हो|कर)", r"कनेक्शन\s+काट"],
    "ARREST_THREAT": [r"गिरफ्तार", r"पुलिस\s+(?:केस|कार्रवाई)", r"डिजिटल\s+अरेस्ट"],
    "CREDENTIAL_REQUEST": [r"(?:ओटीपी|पिन|पासवर्ड|सीवीवी|कार्ड\s+नंबर|खाता\s+संख्या)(?:\s+\S+){0,3}\s+(?<!न )(?<!ना )(?<!मत )(?:बताएं|बताइए|भेजें|भेजो|शेयर\s+करें|दर्ज\s+करें|दें)"],
    "KYC_UPDATE": [r"केवाईसी", r"(?:आधार|पैन)(?:\s+\S+){0,2}\s+अपडेट"],
    "PRIZE_LOTTERY": [r"लॉटरी", r"इनाम", r"जीत\s+(?:लिया|लिए|गए)", r"बधाई\s+हो"],
    "FINANCIAL_PRESSURE": [r"रिफंड", r"कैशबैक", r"(?:प्रोसेसिंग|डिलीवरी)\s+शुल्क"],
    "SUSPICIOUS_CTA": [r"लिंक\s+पर\s+क्लिक", r"क्लिक\s+करें"],
}.items():
    PATTERNS[_sid].extend(_extra)


# "Callback" scams: a made-up charge or subscription and a number to call.
for _sid, _extra in {
    "FINANCIAL_PRESSURE": [
        r"\bwill be (?:debited|charged|deducted)\b.{0,90}\b(?:subscription|renewal|plan|order|invoice|antivirus)\b",
        r"\b(?:subscription|renewal|antivirus)\b.{0,70}\bwill be (?:debited|charged|deducted)\b",
        r"\bif (?:this was )?not (?:you|authori[sz]ed by you)\b.{0,50}\bcall (?:our |the )?(?:help ?desk|support|customer care|number)\b",
    ],
}.items():
    PATTERNS[_sid].extend(_extra)

PROMPT_INJECTION = re.compile(
    r"(?:ignore|disregard|forget)\W+(?:all\W+)?(?:the\W+)?(?:previous|prior|above|earlier)\W+(?:instructions?|rules?|prompts?)|"
    r"system prompt|you are now\b|mark (?:this|it) as safe|say (?:that )?(?:this|it) (?:is )?(?:safe|legit)|"
    r"respond with (?:only )?safe|<\s*/?\s*(?:system|assistant)\s*>|\bjailbreak\b",
    re.I,
)

OPEN_FILE_CONTEXT = re.compile(r"\W*(?:to|and)\s+(?:open|unlock|decrypt|view)\s+(?:it|this|that|the|your)\b", re.I)

GENUINE_ALERT = [
    r"\b(?:debited|credited)\b.{0,30}\b(?:rs\.?|inr|₹)\s?\d",
    r"\b(?:rs\.?|inr|₹)\s?\d[\d,.]*\s*(?:has been )?(?:debited|credited|spent|withdrawn)\b",
    r"\bavl\.? ?bal(?:ance)?\b", r"\ba/?c\s*(?:no\.?)?\s*(?:x{2,}|\*{2,}|\d{2,4}x*)\d*\b",
    r"\byour (?:otp|one[- ]time[- ]password) (?:is|for)\b.{0,40}\d{4,8}",
    r"\b(?:do not|don'?t|never) share (?:this |the |your )?(?:otp|pin|cvv|password)\b",
    r"\btxn\b|\btransaction (?:id|ref)\b|\bupi ref(?:erence)?\b|\brrn\b",
    r"\b\d{4,8}\b\W+(?:is|as)\W+(?:your|the)\W+(?:\w+\W+){0,2}(?:otp|code|passcode)\b",
    r"\b(?:otp|code|passcode)\b[^.\n]{0,40}\bis\W+\d{4,8}\b",
    r"\b(?:do not|don'?t|never) share\b",
]

# Ads and offers: harmless to read, but where their link leads is unknown. Needs two different cues.
PROMO_STRONG = [
    r"\b\d{1,3}\s?% ?(?:off|discount|cashback)\b", r"\bflat\b.{0,20}\boff\b", r"\b(?:sale|offers?(?!\s+(?:letter|you\b|of employment))|discounts?|coupons?|cash ?back|deals?|dhamaka)\b",
    r"\bt&?cs? apply\b|\bterms (?:and|&) conditions apply\b", r"\b(?:marketing|promotional|advertis\w+) (?:e-?mail|message|communication)\b",
    r"\bfree (?:trial|demo|delivery|membership|for (?:one|1|\d+) (?:month|week|day)s?)\b|\btry\b.{0,30}\bfree\b",
    r"\b(?:shop|order|buy|enrol+|sign ?up|register|book)\b\W+(?:\w+\W+){0,2}(?:now|today)\b", r"\bpre-?approved\b|\blifetime[- ]free\b|\bexchange bonus\b",
    r"\beasy apply\b|\bjobs that match\b|\bstart a lesson\b|\bget top prep\b|\buse code\b|\bpromo code\b",
    r"\bwe(?:'re| are) hiring\b|\bjob openings?\b|\bopenings? (?:at|for)\b|\bequal opportunity employer\b",
    r"(?:सेल|छूट|ऑफर|ऑफ़र|डिस्काउंट|सवलत)",
    r"\b(?:upgrade|renew)\b.{0,40}\b(?:plan|offer|fiber|pack|membership|insurance)\b", r"\binvit\w+ you\b|\bearly access\b|\bfirst \w+ free\b",
    r"(?:rs\.?|inr|₹)\s?[\d,]+\s*(?:/|per )\s*(?:month|mo|year|yr)\b", r"\bsite visit\b|\brera\b|\b\d ?bhk\b",
    r"\b(?:festival|festive|diwali|navratri|big billion|great indian)\b.{0,60}\b(?:sale|offers?|shop|starts?)\b", r"\bapply (?:now|instantly|in \d)\b",
    r"\b(?:buy|get) \d+ (?:get|free)\b|\bbogo\b|\bvisit (?:our |the |us at )?(?:store|shop|showroom|outlet)\b",
    r"(?:अभी खरीदें|नियम और शर्तें|खरेदी करा|अटी लागू|शर्तें लागू)",
]

# Everyday notices: needs two different cues. Only used when nothing risky was found.
TRANSACTION_CUES = [
    r"\b(?:debited|credited|deducted|received|withdrawn|paid|pay|payable|spent|refunded|refund)\b", r"\b(?:rs\.?|inr|₹)\s?\d", r"\b(?:upi|neft|imps|rtgs|a/c|acct|account|balance|avl)\b",
    r"\b(?:payment|recharge|transaction|order|booking|ticket|pnr|invoice|receipt|statement|premium|emi|bill|policy|subscription|renews?|appointment|shipment|parcel|package|awb|delivery|delivered|shipped|loan|application|itr|intimation|return|kyc|re-?kyc|branch|tax|penalty|last date|fees?|official (?:banking )?(?:app|application)|mobile banking)\b",
    r"\b(?:successful(?:ly)?|confirmed|approved|generated|processed|failed|due on|due date|will be delivered|out for delivery|has been (?:shipped|delivered|dispatched))\b",
    r"\b(?:sign-?in|login|logged in|password (?:was )?(?:changed|reset)|new device|security alert|otp)\b",
    r"(?:जमा|वजा|डेबिट|क्रेडिट|खाते|खात्या|भुगतान)", r"(?:रुपये|रु\.|संदर्भ|बँक|बैंक|एसबीआई)",
]

PROMO_CUES = [
    r"\b\d{1,3}\s?% ?(?:off|discount|cashback)\b", r"\bflat (?:rs\.?|inr|₹)?\s?\d", r"\bup ?to (?:rs\.?|inr|₹)?\s?[\d,]+ ?(?:off|lakh|cashback)",
    r"\b(?:sale|offers?|discount|deals?|coupon|voucher|dhamaka|clearance|exchange bonus|lifetime[- ]free|pre-?approved|membership)\b",
    r"\bt&?cs? apply\b|\bterms (?:and|&) conditions apply\b",
    r"\b(?:shop|order|book|apply|upgrade|renew|sign ?up|join|claim|download|visit)\b\W+(?:\w+\W+){0,2}(?:now|today|instantly|online|in-?store|your nearest store)\b",
    r"\bunsubscribe\b|\breply stop\b|\blimited (?:period|time)\b|\boffer (?:valid|ends)\b|\bnew launch\b|\bfree (?:trial|delivery|class|demo|membership)\b",
    r"\b(?:invit\w*|referral|refer)\b.{0,40}\b(?:code|friend|earn|get)\b", r"\bcash ?back\b|\bcoupons?\b|\breward points?\b|\bdownload (?:the )?\w+ app\b",
    r"\bsave (?:up ?to )?(?:rs\.?|inr|₹)?\s?\d", r"\bwaived\b|\bearly access\b|\bfirst (?:class|order|month|ride) free\b|\bmaking charges\b",
    r"(?:rs\.?|inr|₹)\s?[\d,]+\s*(?:/|per )\s*(?:month|mo|year|yr|day)\b", r"\b(?:diwali|festive|festival|navratri|holi|christmas|black friday|big billion|great indian)\b",
    r"\b(?:bhk|rera|site visit|booking open|plan|plans|recharge now|upgrade)\b", r"\b(?:new|latest) (?:range|collection|offer|plan|launch)\b",
]

PHONE_RE = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)")
TOLLFREE_RE = re.compile(r"(?<!\d)(?:1-?800|1860)[\s-]?\d{3,4}(?:[\s-]?\d{3,4})?(?!\d)")
EMAIL_RE = re.compile(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", re.I)
UPI_RE = re.compile(r"(?<![\w.])([a-z0-9._-]{2,}@(" + "|".join(sorted(UPI_HANDLES, key=len, reverse=True)) + r"))(?![\w.])", re.I)
IFSC_RE = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")


@dataclass
class MessageAnalysis:
    signals: list[Signal] = field(default_factory=list)
    entities: dict = field(default_factory=dict)
    mentioned_brands: list = field(default_factory=list)  # Brand objects
    genuine_alert: bool = False
    message_type: str | None = None  # otp | transaction | promotion | None


def extract_entities(text: str) -> dict:
    phones = sorted({re.sub(r"[\s-]", "", m.group(0)) for m in PHONE_RE.finditer(text)} | {re.sub(r"[\s-]", "", m.group(0)) for m in TOLLFREE_RE.finditer(text)})
    upis = sorted({m.group(1).lower() for m in UPI_RE.finditer(text)})
    emails = sorted({m.group(0).lower() for m in EMAIL_RE.finditer(text) if m.group(0).lower() not in upis})
    return {"phones": phones, "emails": emails, "upi_ids": upis, "ifsc": sorted(set(IFSC_RE.findall(text)))}


def mentioned_brands(text: str, extra: tuple[str, ...] = ()):
    low = normalize(text)
    found, seen = [], set()
    for token, brand in brand_tokens().items():
        if len(token) < 3 or token in GENERIC_BRAND_WORDS:
            continue
        if re.search(r"\b{re.escape(token)}\b", low) and brand.name not in seen:
            seen.add(brand.name)
            found.append(brand)
    # also the brand's full name written with spaces, e.g. "ICICI Bank"
    for brand in {b for b in brand_tokens().values()}:
        spaced = brand.name.lower()
        if " " in spaced and len(spaced) >= 6 and spaced in low and brand.name not in seen:
            seen.add(brand.name)
            found.append(brand)
    return found


def analyze(text: str, claimed: str | None = None, source: str = "web") -> MessageAnalysis:
    result = MessageAnalysis()
    low = _deleet_words(normalize(text))
    result.entities = extract_entities(text)

    # genuine bank/OTP alert template (needs >= 2 independent matches)
    genuine_hits = sum(1 for p in GENUINE_ALERT if re.search(p, low))
    result.genuine_alert = genuine_hits >= 2

    def add(sid: str, detail: str):
        result.signals.append(make(sid, detail, "message", None))

    for sid, patterns in PATTERNS.items():
        for pattern in patterns:
            for m in re.finditer(pattern, low):
                if sid == "CREDENTIAL_REQUEST":
                    before = low[max(0, m.start() - 70) : m.start()]
                    if NEGATION.search(before + low[m.start() : m.start() + 1]) or NEGATION.search(before):
                        continue
                    if re.match(r"\W*(?:is\W+|:\W*)?\d{4,8}\b", low[m.end() : m.end() + 20]) and re.search(r"otp|code|passcode", m.group(0)):
                        continue  # the code is printed in the message: it is being delivered, not asked for
                    if re.search(r"wi-?\s?fi", m.group(0)):
                        continue  # a Wi-Fi password is not an account secret
                    if OPEN_FILE_CONTEXT.match(low[m.end() : m.end() + 40]):
                        continue  # "enter your password to open it": protects an attachment, not an account
                phrase = re.sub(r"\s+", " ", m.group(0))[:60]
                label = sid.replace("_", " ").lower()
                add(sid, f"Message wording ({label}): \"{phrase}\".")
                break
            if any(s.id == sid for s in result.signals):
                break

    if PROMPT_INJECTION.search(low):
        add("PROMPT_INJECTION", "The text contains instructions aimed at the analysis system.")

    if result.entities["phones"] and any(s.id in {"URGENCY", "FEAR_OR_THREAT", "ARREST_THREAT", "KYC_UPDATE"} for s in result.signals):
        if re.search(r"\b(?:call|contact|whatsapp|dial|helpline|customer care|speak)\b", low):
            add("PHONE_CALL_TO_ACTION", f"Asks you to call {result.entities['phones'][0]} under pressure.")

    if re.search(r"\bsbi\b|\bhdfc\b|\bicici\b|\baxis\b|\bkotak\b|\bpnb\b|\bbank\b", low) and re.match(r"^\+?\d{10,}$", (source or "").replace(" ", "")):
        add("SENDER_PERSONAL_NUMBER", "Claims to come from a bank but was sent from an ordinary phone number.")

    result.mentioned_brands = mentioned_brands(text)

    if re.search(r"\b(?:otp|verification code|security code|passcode)\b", low) and result.genuine_alert:
        result.message_type = "otp"
    elif result.genuine_alert:
        result.message_type = "transaction"
    elif any(re.search(p, low) for p in PROMO_STRONG) and len({i for i, p in enumerate(PROMO_CUES + PROMO_STRONG) if re.search(p, low)}) >= 2:
        result.message_type = "promotion"
    elif len({i for i, p in enumerate(TRANSACTION_CUES) if re.search(p, low)}) >= 2:
        result.message_type = "transaction"

    if result.genuine_alert and not any(s.id in {"CREDENTIAL_REQUEST", "FEAR_OR_THREAT", "ARREST_THREAT", "UPI_COLLECT_SCAM", "PRIZE_LOTTERY"} for s in result.signals):
        result.signals.append(make("GENUINE_ALERT_PATTERN", "The wording matches a standard bank / OTP alert template.", "message", None))

    return result
