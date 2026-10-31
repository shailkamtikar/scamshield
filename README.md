# ScamShield

### An Agentic Multimodal Framework for Explainable Cross-Channel Scam Investigation and Risk Assessment

ScamShield detects and investigates suspicious communications by combining **link intelligence, brand impersonation detection, social-engineering analysis, screenshot OCR + vision, QR/UPI payload analysis, and Gemini-based explanation**.

Unlike detectors that only look at URLs, ScamShield treats the whole message as evidence and produces an **explainable assessment**: a verdict, a risk score, a confidence figure that is computed from the evidence, the reasons, and what to do next.

**Know before you tap.** Paste a message, drop a screenshot or scan a QR code, and ScamShield tells you plainly whether it is safe to open.

---

## Features

- **Message analysis** – finds every link (even without `https://`, defanged, or hidden with look-alike Unicode), follows redirects and shorteners safely, and reads the wording for urgency, threats, OTP/PIN requests, fake KYC, digital-arrest scripts, job and investment scams (English, Hindi, Hinglish). Extracts phone numbers, UPI IDs and emails.
- **Link intelligence** – trusted-domain registry (banks, UPI apps, government, e-commerce, travel, telecom, media and more, India-weighted) plus a popularity list; lookalike / combosquat / gibberish-domain detection; live reputation from Google Safe Browsing, VirusTotal, URLhaus and OpenPhish; domain age; sandboxed page inspection (text only, no scripts run) for login forms and brand impersonation.
- **Screenshots** – Tesseract OCR with pre-processing (dark mode, upscaling) cross-checked by Gemini vision; sender and links are extracted.
- **QR codes** – decoded on the user's phone with the live camera scanner (the link is **never opened**) or from an uploaded image. UPI / Google Pay QRs show payee, address and amount; verified services (Spotify, YouTube, ...) are recognised; unknown links get the full investigation; Wi-Fi, SMS, crypto and unsafe-scheme QRs are handled.
- **Honest verdicts** – `SAFE`, `SUSPICIOUS`, `DANGEROUS`, and `COULD_NOT_VERIFY` (only when a link does not exist or cannot be reached). A gibberish or look-alike domain is `DANGEROUS` even if it does not exist yet.
- **Deterministic scoring** – every point comes from a documented signal weight; the same link scores the same whether typed, read from a screenshot, or scanned.
- **Evidence-based confidence** – computed from how many checks completed and how much of the strong evidence agrees, never invented by the AI.
- **Gemini explanation** – plain-language reasons and recommendation; may raise a SAFE verdict to SUSPICIOUS but can never lower a verdict or change a score. Built-in rules take over if Gemini is unavailable.
- **Live progress** – the UI streams the real pipeline stages (server-sent events).
- **PDF reports** – built in the browser from the actual result; links are defanged.

---

## System architecture

```text
User ── Message / Screenshot / QR (camera or image)
          │
          ▼
       FastAPI  (REST + SSE streaming)
          │
          ▼
  Reader: OCR + Gemini vision (screenshots) · QR decoder + payload classifier (QR)
          │
          ▼
   LangGraph pipeline
     extract ─► message ─► urls ─► decide ─► explain
                              │        │         │
              parse · trust · lookalike  verdict   Gemini (or rules)
              redirects · feeds · age    score     reasons · recommendation
              page inspection            confidence
          │
          ▼
  Explainable result: verdict · score · confidence (+ how computed) · reasons · evidence · per-link inspections
```

---

## Run it locally (Windows)

Prerequisites: Python 3.12 with [`uv`](https://docs.astral.sh/uv/), Node 20+, [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki).

```bash
cd backend && cp .env.example .env     # then fill in the keys (see below)
uv sync
cd ../frontend && npm install
```

Then double-click **`start-local.bat`** (or run `uv run uvicorn app.main:app --port 8000` in `backend/` and `npm run dev` in `frontend/`) and open http://localhost:5173.

**Camera scanner from a phone:** browsers only allow the camera on HTTPS. Run **`start-phone.bat`**, open the `https://<your-pc-ip>:5173` address it prints on a phone on the same Wi-Fi, and accept the self-signed certificate warning. The phone serves the finished build (no live reload), because the dev server's reload WebSocket can loop on phones and show "too many redirects". If the page never opens, allow Node.js through Windows Firewall on private networks.

### Keys (`backend/.env`, never committed)

| Variable | Used for | Required |
|---|---|---|
| `GEMINI_API_KEY` | explanation, screenshot vision | no (built-in rules are used without it) |
| `SAFE_BROWSING_API_KEY` | Google Safe Browsing (v4 Lookup) | no |
| `VIRUSTOTAL_API_KEY` | VirusTotal domain reputation (free tier: 4/min, 500/day) | no |
| `URLHAUS_AUTH_KEY` | abuse.ch URLhaus | no |

OpenPhish and the popular-sites list need no key. Every provider is optional; with fewer sources the engine still answers and reports lower confidence. How to get each key: `docs/playbook/KEYS.md`.

## Tests and accuracy

```bash
cd backend
uv run pytest -q                                   # 81 offline tests
uv run python scripts/evaluate.py                  # URL benchmark, static (no network)
uv run python scripts/evaluate.py --live           # + live threat-feed lookups (never opens suspicious links)
uv run python scripts/eval_messages.py             # SMS benchmark
cd ../frontend && npm test && npm run lint && npm run build
```

Measured numbers and their limits: [docs/STATUS.md](docs/STATUS.md).

## Layout

```
backend/app/intel/    link intelligence (parsing, trust registry, lookalikes, safe fetcher, feeds, domain age, page inspection)
backend/app/engine/   signals + weights, verdict & confidence, message analysis, pipeline steps, explanation
backend/app/qr/       QR payload types, UPI analysis
backend/app/graph/    LangGraph pipeline
backend/app/api/      REST + streaming endpoints
frontend/             React 19 + Vite + Tailwind 4 + Motion
data/benchmark/       labelled links and messages used by the evaluators
docs/                 STATUS, development playbook
```

Deployment (Render + Vercel) is planned in `docs/playbook/08-phase9-release.md` and is not set up yet.
