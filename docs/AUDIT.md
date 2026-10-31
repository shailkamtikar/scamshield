# ScamShield engineering audit

Written after the audit pass of 31 Oct 2026 (commit following `fda14bc`). Every number below was produced by a script in `backend/scripts/` and can be re-run. Where a number is tuned or cannot be trusted, it says so.

## A. What exists

- **Pipeline** (FastAPI + LangGraph): extract links and (if present) parse a raw e-mail → read the wording → check each link → decide → explain.
- **Link engine**: URL parsing and Unicode tricks, trust registry (official / popular / unknown), lookalike and gibberish detection, a small learned domain model, five threat feeds, domain age, redirect following with an SSRF-guarded fetcher, text-only page inspection, optional urlscan.io sandbox.
- **Message engine**: ~25 families of regular-expression rules (English, Hinglish, Hindi), negation handling, scam-script rules, informational-notice logic.
- **E-mail module** (new): if headers or HTML are pasted it reads From / Reply-To / Authentication-Results / attachment names / link text vs link target.
- **Classification layer** (new): every result gets a verdict, a **category** (genuine notice, promotion, spam, phishing, fraud, malicious, suspicious, no problems found) and an **action** (allow, promotional, spam, warn, block, verify).
- **Gemini**: explains the verdict and may raise SAFE to SUSPICIOUS, never anything else; cached; two models with fallback.
- **UI**: dark cinematic design; green safe, blue promotion, grey spam, amber suspicious, red dangerous; category and action shown under the verdict.

## B. Missing functionality (not built, not claimed)

- No DKIM/SPF/DMARC **verification**; only the receiving server's own result header is read, and only if pasted.
- No Tamil / Telugu / Bengali / Gujarati / Kannada / Malayalam **wording** rules. Messages in those languages are caught only when their link is bad.
- No JavaScript execution or real-browser inspection of our own; a real sandbox exists only through urlscan.io with a key (not tested live).
- No attachment content scanning (names only). No WhatsApp or e-mail account integration; input is pasted text, screenshots and QR codes.
- No user accounts, history or feedback loop.

## C. Is the category split correct?

Mostly, for common cases; not for everything. On 145 hand-written scenarios (below) genuine notices, promotions, phishing and fraud separate well. Weak spots: cold B2B outreach and "follower-selling" spam is not recognised as spam; scammy spam with a link ("free gifts, click here") is called *suspicious* rather than spam; an advert that impersonates a brand is called phishing, not spam. Spam versus a scam is a judgement call in places, and the labels here are ours.

## D. Measured performance (rules only unless stated; no AI calls)

| Set | What it is | Result |
|---|---|---|
| `redteam.csv` (75) | hand-labelled scenarios from the brief. **Used for development, so tuned.** | 92 % category right, 2.6 % false alarms, 0 % missed malicious |
| `redteam_blind.csv` (40) | written fresh, run once, then used for fixes. **Now tuned.** First run 72.5 % category right and 31 % of malicious called benign; after fixes 87.5 %, 0 % / 0 %. | |
| `redteam_sealed.csv` (30) | written last, run once before any fix. **The honest figure.** | **63 % category right** on first run (that run also had a bug, below); after generic fixes 67 %; false alarms 2/17 (both are scammy spam called suspicious), 0 malicious missed |
| `messages_genuine.csv` (105 genuine + 20 ads) | genuine notices across sectors | 0 / 125 flagged (first run 11 / 105 genuine) |
| your 17 real messages and ads (private, git-ignored) | real SMS, e-mails, adverts | 0 / 17 flagged |
| `messages.csv`, `messages_handwritten.csv` | template / tuned sets | 100 % / 0 % false alarms (not independent) |
| `messages_heldout.csv` (48) | written after the first freeze | **62.5 % detection, 0 % false alarms** rules only (it was 50 % / 4 %); 96 % with Gemini measured earlier, not re-run |
| `urls.csv` (1,228 links, static) | links, no network | 84.4 % detection, 1.6 % false alarms; live checks raise it (see STATUS) |
| e-mail benchmark + 9 header tests | formal e-mails, spoofing, attachments, hidden links | 0 false alarms, 0 missed, all 9 header tests pass |

Per-category precision / recall / F1 and the confusion matrix print from `uv run python scripts/eval_redteam.py --file <set>`. Typical latency 5 ms per message offline; peak Python memory about 20 MB. Network checks add 1–10 s.

**Against your 95 % target:** not reached on independent data. The honest independent figure for category on brand-new scenarios is about 65–70 % (rules alone); malicious versus benign (ignoring which category) is much better: 0 malicious missed and 2/17 benign flagged on the sealed set. Gemini's second opinion is what lifts unseen scripts, and it was not re-measured.

A bug found and fixed during this audit: a bulk text edit had removed an `f` prefix and silently disabled brand detection in messages. It lowered the first blind and sealed numbers; both are reported as they were measured.

## E. False alarms

Sealed set: `Lucky Dhamaka … free gifts … click http://rch-gift-offer.xyz` and `Get 1000 YouTube subscribers … Cheapest SMM panel` (both called suspicious; arguably right, labelled spam by us). Dev set: an instant-loan spam ad (suspicious). Real messages: none.

## F. Missed malicious

None on the three red-team sets after the fixes. Before fixes (blind set, first run): digital-arrest call, "read out the 6-digit code", customs-duty UPI scam, WhatsApp part-time job, crypto "make you rich". Sealed set, first run: sextortion and remote-support scams. These classes are now covered by rules; new variants will still slip past rules.

## G. URL detection

Works: lookalikes, combosquats, gibberish, homographs, userinfo tricks, raw / encoded IPs, brand-in-subdomain (now also on popular domains), shorteners, redirect chains, five threat feeds, domain age, `*.bank.in` / gov / edu zones. Limits: a brand-new phishing site on a clean-looking domain with a JavaScript-only page can be missed (about 8 % in our test); "no threats listed" is reported as "no problems found", never as safe.

## H. Website detection

Text-only inspection of HTML (title, forms, password fields, cross-domain form posts, brand mismatch, hosting-provider warning pages) measured on 560 real pages. No scripts run, nothing is executed. Real-browser sandboxing only via urlscan.io (needs a key; not verified live).

## I. Gemini

Reliable by design, not by measurement of this session. Good: message text is fenced and declared untrusted (and the fence characters are now neutralised), output is schema-checked, it cannot lower or raise a verdict beyond SAFE→SUSPICIOUS and needs an exact quote of a concrete ask, cached (now bounded at 500 entries), rate-spaced, 10 s timeout, falls back to rules when unavailable. It is never given invented sender or domain facts. Weakness: accuracy on unseen scripts depends on it, and free-tier quota can run out.

## J. Security audit

| Finding | Status |
|---|---|
| DNS rebinding: the fetcher resolved a name, then connected using a second lookup | **Fixed**: connects to the validated IP; Host header and TLS name preserved; test added |
| Private / loopback / metadata addresses, odd ports, scheme, redirects re-validated per hop, size and time limits | Already in place, re-tested |
| Pillow 12.3.0 (image uploads) had 39 known advisories; also certifi, urllib3, pyasn1, langgraph-sdk | **Fixed** (upgraded; `pip-audit` now clean) |
| DOMPurify advisory via the PDF library | **Fixed** (`npm audit` 0) |
| Gemini cache unbounded | **Fixed** (500 entries) |
| Prompt-injection fence could be closed by the text itself | **Fixed** |
| Message length raised to 40,000 characters (pasted e-mails). Checking showed two regular expressions (UPI id, e-mail address) took 7 s on a 40,000-character run of one symbol: a cheap way to tie up the server | **Fixed**: bounded and anchored; worst case now about 0.6 s; test added |
| API has no login; optional API key and per-IP rate limits only | **Open** (fine for a demo, not for a public launch without a key or gateway) |
| No penetration test, no fuzzing of the e-mail / image parsers | **Open** |
| Logs never contain message text | Verified in code |

## K. Remaining limits

Categories beyond common cases depend on hand-written rules; rules-only coverage of unseen scam scripts is the main weakness. Spam recognition is heuristic. Non-Hindi Indian-language wording is untested. The camera scanner has not been tried on a real phone. Nothing has been deployed or load-tested. The 125 genuine and 145 red-team messages were written by us, not collected from real traffic, so real-world false alarms are unknown beyond your 17 real messages.

## L. Readiness (out of 10, with reasons)

| Area | Score | Why |
|---|---|---|
| Message classification | 6 | Good on common scripts and genuine notices; 67 % category on first-seen scenarios |
| E-mail detection | 5 | Header, attachment and hidden-link logic works on 9 hand-made e-mails; no real header corpus; no DKIM verification |
| Spam detection | 4 | Heuristic: recognises ads without an identifiable sender or with an unverified link; misses cold outreach |
| Promotional detection | 7 | 0 false flags on 30 real/hand-written ads; 14/20 identified as brand promotions |
| Financial-fraud detection | 6 | Many Indian scripts covered; rules-only recall on unseen wording about 60–90 % |
| URL detection | 7 | 84 % static, ~92 % with page checks, 1.6–2.6 % false alarms; day-zero sites remain hard |
| Website detection | 5 | Text-only inspection; sandbox optional and unverified |
| Sender authentication | 3 | Only reads a pasted result header |
| Machine-learning quality | 4 | Two small learned models (domain names); text ML was tried and rejected; training data not re-audited this session |
| Gemini integration | 6 | Safe design, graceful fallback; accuracy contribution not re-measured |
| Application security | 7 | Fetcher hardened, dependencies clean; no authentication, no pen-test |
| Production readiness | 5 | Not deployed, no real-user trial, no monitoring yet |

## Addendum: how-to and instruction mails (ICICI "login with mobile number")

A real ICICI mail explaining how to log in with a mobile number and OTP was marked suspicious (25). Cause: "enter the OTP received on your registered number" was read as a request for a secret, although the only link was the bank's own `*.bank.in` address. The class fixed: **instruction wording is not a request.** A credential ask is only a risk when there is a way to hand the secret to someone or somewhere we cannot verify (share / send / read out / reply, a mobile number, an unknown link, WhatsApp). Also fixed in the same pass:

- Several *moderate* hints together (e.g. "disconnect", "pending bill", "names X but links elsewhere") can no longer add up to DANGEROUS; one strong finding is required.
- A domain our lists do not know but which is named after the organisation in the message, is over 5 years old and clean in every feed is treated as that organisation's own address (live checks only; offline there is no age).
- `*.bank.in`, `*.fin.in`, `*.gov.in` etc. now say what they are ("a licensed Indian bank") instead of "Government / academic domain".
- "office", "windows", "outlook", "teams" and similar everyday words are no longer read as brand names.

New test set `genuine_longform.csv` (25 how-to / notice mails: payments, ATM and card activation, UPI mandate approval, e-verify, UAN, SIM re-verification, returns, renewals): 5 were flagged on first run, 0 now offline (24 offline, the 25th needs the live checks). Guard tests confirm the same wording **with a hand-over channel** (read out to an executive, reply with the OTP, unknown link, mobile number, Hinglish "OTP bhejein") is still flagged. Total tests: 313 backend, 9 frontend.

**The link decides (31 Oct).** When every link in a message is a verified address (official, well-known, or an established same-name domain; no shorteners or open platforms) and nothing else in it can take you somewhere unverified, persuasive wording (urgency, KYC, prizes, "guaranteed returns", work-from-home) is no longer scored. Still flagged even with a verified link: handing a code to a person, paying a fee, installing a remote-access or APK app. The urlscan.io real-browser sandbox was re-tested live with the configured key: scan finished in 18 s with final address, page title, domain age and screenshot.

## How to re-run everything

```bash
cd backend
uv run pytest -q
uv run python scripts/eval_redteam.py --file redteam.csv --show
uv run python scripts/eval_redteam.py --file redteam_blind.csv
uv run python scripts/eval_redteam.py --file redteam_sealed.csv
uv run python scripts/eval_genuine.py --show
uv run python scripts/eval_emails.py
uv run python scripts/evaluate.py
```
