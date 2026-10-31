# ScamShield – build status

Local build (phases 0–8). Deployment is not done yet.

## What was verified

| Area | State | Evidence |
|---|---|---|
| Message, screenshot and QR analysis | Done | 114 backend tests, benchmarks below, run through the real UI |
| Link checks (structure, lookalikes, redirects, feeds, domain age) | Done | live runs against Google Safe Browsing, VirusTotal, URLhaus, OpenPhish, Phishing.Database |
| **Page inspection (text-only "sandbox")** | Done, calibrated on 560 real pages | see below |
| **Browser sandbox (urlscan.io)** | Built and tested with mocked responses; **only earlier public scans are used until a `URLSCAN_API_KEY` is added** | tests; not run against a live submission |
| Learned domain-name model | Done | trained on 159k real phishing domains vs. 950k ordinary ones; 0.90 AUC on unseen OpenPhish domains |
| Live camera QR scanner | Built; **not tested on a real phone** | error handling verified only |
| Frontend (dark cinematic UI, restored on request) | Done | lint, 8 unit tests incl. PDF, production build, manual runs |
| CI | Workflow present; result not checked from here | check the Actions tab |
| Deployment | **Not done** | |

## What the "sandbox" really is

Two different things, and they should not be confused:

1. **Text-only page inspection (built in, always on).** The server downloads a link's HTML *as text* (no scripts run, nothing saved, size and time capped, private addresses blocked) and looks at the title, forms and links. Measured on 560 real pages: it works on about 85–90 % of sites, but ~16–23 % of pages are blank without JavaScript, so it cannot see them. Findings are used carefully: an ordinary login form is only a weak signal (it appeared on 6.6 % of safe sites); a hosting provider's own "Suspected phishing" warning page (46 % of the phishing pages sampled) is treated as decisive.
2. **Real-browser sandbox (urlscan.io, optional).** urlscan opens the link in an isolated browser on its own machines and returns a verdict, final address, domain age and a screenshot. Without a key we can only reuse scans others already made. With a key, new scans are submitted as *unlisted* and take about 10–25 seconds. This is the part that sees JavaScript-only pages.

## Accuracy, measured honestly

Gates agreed with the sponsor: detection ≥ 90 %, false positives ≤ 3 %, overall ≥ 90 %. "Dead" links (don't exist) are reported as *couldn't verify* and are excluded from these counts.

### Links (`backend/scripts/evaluate.py`)

| Condition | Detection of phishing | False alarms on safe sites |
|---|---|---|
| No network at all (structure + trust + learned model only) | 84.6 % | 1.6 % |
| **Brand-new phishing: all threat feeds switched off, but links followed and pages inspected** | **91.9 %** | **2.6 %** (13 of 492 live safe sites) |
| Everything on, feeds included | 100 % (partly by construction: the test links come from those feeds) | same as above |

The 91.9 % row is the honest figure for phishing nobody has listed yet. It still leans on hosting providers' own warning pages, which only exist for pages already reported to them, so a truly day-zero site on a clean-looking domain can be missed. Most remaining false alarms are random-string domains found in popularity lists (e.g. `qihuiwzf.com`), which the engine flags on purpose.

**Confidence is meaningful:** results the engine rated ≥ 0.9 were right 98–100 % of the time; the phishing it missed carried confidence below 0.8, labelled "no problems found" rather than "safe".

### Messages (`backend/scripts/eval_messages.py`)

| Set | Rules only | With Gemini second opinion |
|---|---|---|
| 542 template messages (written with the rules, so not independent) | 100 % / 0 % false alarms | – |
| 51 hand-written messages (tuned afterwards, so not independent) | 100 % / 0 % | – |
| **48 messages written after the engine was frozen (`messages_heldout.csv`)** | **54 % detection, 8 % false alarms** | **96 % detection, 8 % false alarms** (one miss: a Telegram investment link) |

So the *rules alone* miss scams written in wording they weren't designed for; Gemini's second opinion is what catches them. If Gemini is unavailable (no key, quota, outage) the engine falls back to the rules and accuracy on new scam scripts drops to roughly the first column. A learned local text model was tried and **rejected** because it did poorly on this held-out set (71 % detection, 29 % false alarms).

## Hardening added

Per-IP rate limits (429 with Retry-After), optional access key, request ids, security headers, logs that never contain message text, hard time limits on link fetching, Hindi (Devanagari) scam patterns, multi-QR images through the streaming path, "valid payment request" and "no problems found" distinguished from "verified safe".

## Known limits

- Day-zero phishing on a clean-looking domain can still be missed.
- Gemini free tier: ~2 s with the light model first, with timeouts; without it, new scam wording is caught less often.
- VirusTotal free tier is 4 lookups/min (used only for unknown domains, cached).
- Tesseract has English only locally; Hindi screenshots depend on Gemini vision.
- A valid UPI QR is reported as a valid request; the payee's real identity can't be verified.
- Free-hosting pages (github.io, pages.dev, …) are never auto-trusted and are at least *suspicious*.

## Run the checks

```bash
cd backend && uv run pytest -q
uv run python scripts/evaluate.py                              # static
uv run python scripts/evaluate.py --full --blind --only phish  # new phishing, feeds off
uv run python scripts/evaluate.py --full --only safe           # false alarms on live safe sites
uv run python scripts/eval_messages.py --file messages_heldout.csv --llm
uv run python scripts/measure_sandbox.py --n 120               # what page inspection sees
cd ../frontend && npm test && npm run lint && npm run build
```
