# ScamShield – build status

Last updated at the end of the local build (phases 0–8 of `docs/playbook`). Deployment (phase 9) is intentionally not done yet.

## What works (verified)

| Area | State | How it was verified |
|---|---|---|
| Message analysis | Done | 97 offline backend tests, two message benchmarks (below) |
| Link intelligence (parse, trust registry, lookalikes, gibberish, redirects, feeds, domain age, page inspection) | Done | unit tests, URL benchmark, live checks against Google Safe Browsing / VirusTotal / URLhaus / OpenPhish with the team's keys |
| Screenshot reading (OCR + Gemini vision) | Done | generated light/dark SMS screenshots read correctly and scored correctly; OCR unit tests |
| QR codes (image upload) | Done | generated codes incl. rotated, small, multi-code images; UPI, Spotify, URL, Wi-Fi, crypto, `javascript:` payloads |
| Live camera QR scanner | Built and unit-tested; **not tested on a real phone** (the in-app browser blocks the camera) | error handling verified; use `start-phone.bat` to test on a phone |
| Streaming progress (SSE) | Done | API tests (event order, error events) and seen live in the UI |
| Frontend (cinematic dark UI, mobile, PDF report, verdict-tinted scenes) | Done | lint, 6 unit tests, production build, manual run-through of scam / safe / mobile layouts |
| CI | Workflow added (`.github/workflows/ci.yml`); result not checked from here | check the repo's Actions tab |
| Deployment (Render / Vercel / uptime monitor) | **Not done** | needs your accounts; see `docs/playbook/08-phase9-release.md` |

## Accuracy – measured, with caveats

Gates agreed with the sponsor: detection ≥ 90 %, false positives on safe links ≤ 3 %, overall ≥ 90 %.

### Links (`backend/scripts/evaluate.py`, benchmark in `data/benchmark/urls.csv`)

The bad links are real feed entries (OpenPhish) plus synthetic scam patterns; the safe links are popular sites the engine's trust list does **not** contain (Tranco rank 50k–400k), curated real sites, and "login-style" paths on real sites.

| Mode | Detection | False positives | Accuracy |
|---|---|---|---|
| **Static** (no network: structure, lookalikes, trust list only) – n = 1,228 | 82.9 % | 1.6 % | 91.6 % |
| **Live** (adds Safe Browsing / URLhaus / OpenPhish lookups, never opens the links) – held-out test split, n = 253 | 99.1 % | 2.2 % | 98.4 % |

Read these honestly:
- Static detection of **real feed phishing** is ~60–70 %: many real phishing pages sit on innocent-looking or hacked sites that nothing in the address gives away. Those are caught only if a feed has already listed them, or by page inspection when the page can be fetched.
- The live detection figure is high partly *because* the benchmark's phishing links come from the same feeds the engine queries. A brand-new phishing site that no feed has seen yet will behave like the static figure. The 90 % goal for completely unseen phishing is **not** demonstrated.
- Most of the benchmark's "false alarms" are random-string domains (e.g. `qihuiwzf.com`) that happen to be in the popularity list; the engine calls them dangerous on purpose (gibberish domains). Treat them as arguable rather than clear errors.
- Malware-download links (e.g. files hosted on github.com) are a different problem from phishing and are excluded from the gate (`--include-malware` shows them).

### Messages (`backend/scripts/eval_messages.py`)

| Set | Detection | False positives |
|---|---|---|
| 542 template-generated India-focused messages (`messages.csv`) | 100 % | 0 % |
| 51 hand-written messages (`messages_handwritten.csv`) | 100 % | 0 % *after tuning*; the first, untuned run was 85.7 % detection and 4.3 % false positives |

The template set was written together with the rules, so its 100 % says little. The hand-written set was a fair test only on its first run (85.7 % / 4.3 %); after fixing the misses it is no longer independent. Real SMS from the sponsor would be the proper test.

## Known limits

- New phishing sites on clean-looking domains can slip through until feeds list them (see above).
- Free tiers: VirusTotal allows 4 lookups/minute and 500/day (used only for unknown domains, cached 24 h); if a source is down or over quota the engine still answers with lower confidence.
- OCR language: only English is installed locally for Tesseract; Hindi screenshots rely on Gemini vision. Install `tesseract-ocr-hin` to add Hindi OCR (the deployment image will include it).
- The page inspector reads HTML text only and never runs scripts; phishing kits that hide from servers can look harmless.
- Pages hosted on free platforms (github.io, pages.dev, blogspot, …) are never auto-trusted and are at least `SUSPICIOUS`.
- A valid UPI QR is reported as a valid payment request; the payee's real identity cannot be verified, so the report shows payee and amount for the user to confirm and confidence is capped at 80 %.
- Gemini free tier: the lighter model answers in ~1–2 s and is used first; the stronger one is the fallback. Without a key everything still works with built-in explanations.

## Verification commands

```bash
cd backend && uv run pytest -q                                  # 97 passed
uv run python scripts/evaluate.py                               # static URL benchmark
uv run python scripts/evaluate.py --live --split test           # live-feed URL benchmark (no links opened)
uv run python scripts/eval_messages.py                          # template messages
uv run python scripts/eval_messages.py --file messages_handwritten.csv
cd ../frontend && npm test && npm run lint && npm run build
```

## Changes from the original playbook

- Everything is committed to `main` (as requested), with phase tags `v0.1-baseline` and `phase-0-done`.
- Google Safe Browsing uses the v4 Lookup API; v5 only answers in a binary format.
- The three benchmark sets are generated by scripts (`build_benchmark.py`, `gen_messages.py`) and committed as CSVs; raw feed downloads stay git-ignored.
- Light mode was dropped; the UI is dark-only with verdict-tinted scenes.

## Before the sponsor demo

1. Run `start-local.bat`; try the built-in examples (fake KYC, genuine bank alert, dead link, courier scam).
2. Test the camera scanner on a phone with `start-phone.bat` (Google Pay QR, Spotify QR, a QR to a fake link).
3. Check the GitHub Actions result.
4. Decide on deployment (Render + Vercel + uptime monitor); the Dockerfile and `render.yaml` are the next work item.
