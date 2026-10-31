# Phase 0 - Project Setup & Baseline

Branch: work directly on `main` (push after every verified milestone).

---

## Milestone 0.1 - Baseline snapshot and repo hygiene

**1. Name:** Freeze the current prototype as a known-good baseline.
**Depends on:** nothing.

**2. Objective:** The working tree has 6 uncommitted edits (`gemini_reasoning.py`, `url_investigation.py`, `signals.py`, `state.py`, `domain_analysis.py`, `test_cross_modal_consistency.py`). Capture them as a verified baseline so every later change can be diffed and reverted against it.

**3. Tasks**
- [ ] `git status` / `git diff` review of the 6 modified files; confirm no secrets.
- [ ] Run the existing scripts by hand and note which pass/fail (they are scripts, not a suite).
- [ ] Confirm `.gitignore` covers `.env`, `.venv`, `node_modules`, `dist`, `__pycache__` (it does) and add `data/raw/`, `data/cache/`, `*.log`, `.coverage`, `htmlcov/`.
- [ ] Confirm `git config user.name/email` are yours; run the co-author audit from `00-README.md`.
- [ ] Commit baseline; tag `v0.1-baseline`.

**4. Files:** `.gitignore`, the 6 modified files (no content change).

**5. Guidance:** Commit the existing edits unchanged. Do not refactor yet. A tag is the cheapest rollback anchor for the entire project.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 0.1-T1 | Backend boots | `.env` has `GEMINI_API_KEY` | `cd backend; uv sync; uv run uvicorn app.main:app` ; open `/` | `{"project":"ScamShield",...}` | [ ] |
| 0.1-T2 | Text endpoint baseline | T1 running | POST `/investigate` with the demo message (Microsoft / `miconsoft-login.com`) | 200, `risk_level` HIGH or CRITICAL, evidence lists impersonation | [ ] |
| 0.1-T3 | Frontend builds | `npm ci` done | `cd frontend; npm run build` | exit 0 | [ ] |
| 0.1-T4 | Secret scan | staged changes | secrets-leak command from README | prints `ok` | [ ] |
| 0.1-T5 | No co-author | after commit | co-author audit | prints `clean` | [ ] |
| 0.1-T6 | Missing key (negative) | unset `GEMINI_API_KEY` | start backend | fails with the clear RuntimeError (documents current behaviour; changed in 0.3) | [ ] |

**7. Verification:** [ ] T1-T6 pass [ ] `git status` clean after commit [ ] tag exists locally.
**8. Completion:** baseline committed and tagged; behaviour recorded.

**9. Git**
```bash
git status
git add .
git commit -m "chore: baseline snapshot of prototype before production rework"
git tag -a v0.1-baseline -m "Prototype baseline"
git push origin main --tags
```
Not committed: `.env`, `.venv`, `node_modules`, `frontend/dist`.
**10. Rollback:** nothing depends on this; if wrong, R1. The tag is the permanent anchor.

---

## Milestone 0.2 - Close the arbitrary-file-read hole

**1. Name:** Remove client-controlled `image_path`.
**Depends on:** 0.1.

**2. Objective:** `InvestigationRequest.image_path` lets any caller make the server OCR a file on its own disk (`screenshot_analysis_node`). Remove it; images only enter via upload endpoints.

**3. Tasks**
- [ ] Delete `image_path` from `backend/app/models/investigation.py`.
- [ ] Stop passing it in `backend/app/api/investigate.py`.
- [ ] Remove `screenshot_analysis_node` from `graph.py` (the upload endpoint already OCRs before the graph) and delete the node file.
- [ ] Remove `image_path` from `ScamShieldState`.
- [ ] Add `extra="forbid"` to the request model so unknown fields return 422.

**4. Files:** `app/models/investigation.py`, `app/api/investigate.py`, `app/graph/graph.py`, `app/graph/state.py`, delete `app/graph/nodes/screenshot_analysis.py`, `test_screenshot_node.py`.

**5. Guidance:** pydantic `model_config = ConfigDict(extra="forbid")`. Upload endpoints already write to a temp file and delete it in `finally`; keep that.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 0.2-T1 | Path injection blocked | server up | POST `/investigate` with `{"message":"hi","image_path":"C:/Windows/win.ini"}` | 422 | [ ] |
| 0.2-T2 | Normal text still works (regression) | server up | demo message | 200, same fields as 0.1-T2 | [ ] |
| 0.2-T3 | Image upload still works (regression) | `test_screenshot.png`, Tesseract installed | POST `/investigate/image` | 200, `extracted_text` non-empty | [ ] |
| 0.2-T4 | QR upload still works (regression) | a QR png | POST `/investigate/qr` | 200 with `decoded_text` | [ ] |
| 0.2-T5 | Unknown extra field | server up | POST with `{"message":"x","foo":1}` | 422 | [ ] |

**7. Verification:** [ ] T1-T5 [ ] `grep -r image_path backend/app` returns nothing [ ] graph still compiles (`uv run python -c "import app.graph.graph"`).
**8. Completion:** no code path reads a client-supplied file path.

**9. Git**
```bash
git status
git add .
git commit -m "security: remove client-supplied image_path and redundant screenshot node"
git push origin main
```
**10. Rollback:** R2 (`git revert <hash>`); no data or env impact.

---

## Milestone 0.3 - Central configuration and environment

**1. Name:** Env-driven settings.
**Depends on:** 0.2.

**2. Objective:** Remove hardcoded values (`TESSERACT_PATH` Windows path, localhost CORS, mandatory Gemini key at import) so the same code runs locally, in Docker and on Render.

**3. Tasks**
- [ ] Add `pydantic-settings` and create `Settings` in `app/config.py` with: `GEMINI_API_KEY` (optional, engine degrades to rules-only if absent), model names, `TESSERACT_CMD` (default: `shutil.which("tesseract")`), `CORS_ORIGINS` (comma list), and placeholders for later keys: `SAFE_BROWSING_API_KEY`, `VIRUSTOTAL_API_KEY`, `URLHAUS_AUTH_KEY`, `API_ACCESS_KEY`.
- [ ] `ocr.py` reads the path from settings.
- [ ] `main.py` reads CORS from settings.
- [ ] Update `backend/.env.example` with every variable (empty values).
- [ ] Startup log line lists which optional providers are configured (never the keys).
- [ ] Verify the Gemini model names against your key with a one-off script (`client.models.list()`).

**4. Files:** `app/config.py`, `app/services/ocr.py`, `app/services/gemini.py`, `app/main.py`, `backend/.env.example`, `pyproject.toml`.

**5. Guidance:** Why `pydantic-settings`: already using pydantic, gives typed env parsing and one place to validate. Gemini client must be created lazily so tests can import modules without a key.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 0.3-T1 | Boots without Gemini key | key unset | start server, GET `/` | 200 (no crash) | [ ] |
| 0.3-T2 | CORS from env | `CORS_ORIGINS=http://localhost:5173,https://x.vercel.app` | preflight OPTIONS from each origin | allowed; other origin rejected | [ ] |
| 0.3-T3 | Tesseract auto-detect | Tesseract on PATH, `TESSERACT_CMD` unset | POST `/investigate/image` | OCR works on Windows and in Linux container | [ ] |
| 0.3-T4 | Bad `TESSERACT_CMD` (failure) | env set to nonexistent path | upload image | clean 503 with message, not a stack trace | [ ] |
| 0.3-T5 | Gemini missing at request time | key unset | POST `/investigate` demo | 200, rules-only result, `reasoning_model==""` | [ ] |
| 0.3-T6 | Model availability | real key | run list-models script | both configured models appear, else update `.env` | [ ] |

**7. Verification:** [ ] T1-T6 [ ] `.env.example` lists every variable [ ] `grep -rn "C:\\\\" backend/app` empty.
**8. Completion:** no hardcoded paths/origins; app starts with zero keys.

**9. Git**
```bash
git status
git add .
git commit -m "feat(config): env-driven settings, optional Gemini, configurable CORS and Tesseract"
git push origin main
```
Never commit your real `.env`.
**10. Rollback:** R2. If deployed envs were changed later, keep variable names stable.

---

## Milestone 0.4 - Real test harness

**1. Name:** pytest suite replacing loose scripts.
**Depends on:** 0.3.

**2. Objective:** Offline, repeatable tests with mocked Gemini and mocked network, so every later milestone can prove no regression.

**3. Tasks**
- [ ] `uv add --dev pytest pytest-cov respx httpx` (respx mocks httpx used from Phase 2).
- [ ] Create `backend/tests/` with `conftest.py` (FastAPI `TestClient`, a fixture that patches `analyze_scam_evidence`).
- [ ] Port each `test_*.py` script into `tests/` as assertions; delete the scripts once ported.
- [ ] Add `[tool.pytest.ini_options]` with marker `live`.
- [ ] Add `.github/workflows/ci.yml` running `uv run pytest -m "not live"` and `npm run lint && npm run build` on push (free for public repos).

**4. Files:** `backend/tests/*`, `backend/pyproject.toml`, `.github/workflows/ci.yml`; delete old `backend/test_*.py`.

**5. Guidance:** CI keeps secrets out: the suite must pass with no keys.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 0.4-T1 | Suite runs offline | no internet/no keys | `uv run pytest -m "not live" -q` | all pass | [ ] |
| 0.4-T2 | Gemini mocked | fixture active | POST `/investigate` | no network call made | [ ] |
| 0.4-T3 | Regression: domain compare | none | assert `compare_domains("Microsoft","miconsoft-login.com")["possible_typosquatting"]` | True | [ ] |
| 0.4-T4 | Regression: dedupe | none | same URL twice in message | one URL extracted | [ ] |
| 0.4-T5 | Deliberate fail | temp break a rule | run suite | goes red (proves tests detect breakage); revert | [ ] |
| 0.4-T6 | CI | push branch | GitHub Actions | green check | [ ] |

**7. Verification:** [ ] coverage report generated [ ] CI green [ ] old scripts removed.
**8. Completion:** one command proves the project works offline.

**9. Git**
```bash
git status
git add .
git commit -m "test: pytest harness, mocked Gemini, CI workflow"
git push origin main
```
Not committed: `.coverage`, `htmlcov/`.
**10. Rollback:** R2; deleted scripts are recoverable from `v0.1-baseline`.

---

## Phase 0 Completion Checkpoint
| Item | Record |
|---|---|
| Completed milestones | 0.1, 0.2, 0.3, 0.4 |
| Tests passed | all `0.x-T*` |
| Known issues | (fill in) |
| Git hash | `git rev-parse --short HEAD` |
| Overall verification | clean checkout -> `uv sync` -> `pytest` green -> app boots with no keys |
| Go/No-Go | Go only if CI green and security hole closed |

```bash
git tag -a phase-0-done -m "Phase 0 complete" && git push origin main phase-0-done
```

---

# Phase 1 - Benchmark Dataset & Evaluation Harness

Branch: work directly on `main` (push after every verified milestone).
Purpose: you cannot claim 85-90 % without a measuring stick. Build it before the engine, so every change is judged by numbers.

## Milestone 1.1 - URL benchmark set

> **KEY GATE A:** before starting, stop and ask the user for the abuse.ch Auth-Key using `KEYS.md` (Gate A). OpenPhish and Tranco need no key.

**1. Name:** Labelled URL corpus (phishing vs safe).
**Depends on:** Phase 0.

**2. Objective:** >= 600 phishing URLs and >= 600 safe URLs, labelled, with category tags, reproducible by script.

**3. Tasks**
- [ ] `backend/scripts/fetch_feeds.py` downloads: OpenPhish community feed, URLhaus recent-URL CSV (needs abuse.ch Auth-Key), optionally PhishTank. Output to `data/raw/` (git-ignored).
- [ ] Safe set: Tranco top-N domains (sampled across rank bands, not just the top 100), plus a hand-curated `data/benchmark/safe_india.csv` of real Indian sites across categories (banks, government `.gov.in`, e-commerce, travel, telecom, education, news, delivery, jobs, health, streaming).
- [ ] Synthetic bad set `data/benchmark/synthetic_bad.csv`: generated lookalikes (typosquats, homoglyphs, `brand-login-verify.xyz` combos, raw IPs, gibberish domains, shortened links) so detection of NEW sites is tested.
- [ ] Build `data/benchmark/urls.csv` with columns `url,label,category,source`. Keep only the curated/synthetic CSVs and a small fixed sample (<= 200 rows) in git; the bulk is regenerated.
- [ ] Dedupe by registrable domain; freeze with a date in `data/benchmark/README.md`.

**4. Files:** `backend/scripts/fetch_feeds.py`, `backend/scripts/build_benchmark.py`, `data/benchmark/*`, `.gitignore`.

**5. Guidance:** Live phishing URLs are short-lived; label from feed at fetch time and never visit them from your own browser. Tranco is used for safe sampling because popularity is a reasonable (not perfect) proxy for legitimacy; curate by hand where Tranco is wrong.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 1.1-T1 | Build runs | keys in env | `uv run python scripts/build_benchmark.py` | `urls.csv` created | [ ] |
| 1.1-T2 | Schema | csv exists | pytest validates columns, labels in {safe,phish} | pass | [ ] |
| 1.1-T3 | Balance | csv exists | count labels | each >= 600 (or documented reason) | [ ] |
| 1.1-T4 | No duplicates | csv exists | dup registrable domains | none | [ ] |
| 1.1-T5 | Feed outage (failure) | block one feed | run script | warns, continues with others | [ ] |
| 1.1-T6 | Safe set sanity | csv exists | spot check 30 random safe rows manually | all are genuine sites | [ ] |

**7. Verification:** [ ] counts recorded [ ] `data/raw` untracked [ ] README documents sources and date.
**8. Completion:** reproducible labelled corpus.

**9. Git**
```bash
git status
git add .
git commit -m "feat(benchmark): URL corpus builder and curated safe/synthetic sets"
git push origin main
```
Not committed: `data/raw/`, feed dumps, keys.
**10. Rollback:** R2; delete `data/raw` locally.

## Milestone 1.2 - Message (SMS) benchmark set

**1. Name:** Labelled scam/safe message corpus.
**Depends on:** 1.1.

**2. Objective:** >= 300 scam and >= 300 genuine messages, Indian context, covering many scam types.

**3. Tasks**
- [ ] Scam templates (parametrised with brand, amount, link): fake KYC / account block, electricity disconnection, courier/customs fee, fake job / work-from-home, lottery / KBC prize, loan apps, income-tax refund, Aadhaar/PAN update, UPI collect request, investment/crypto groups, OTP theft, parcel redelivery, digital arrest / police, utility / FASTag, tech support, romance, delivery with `bit.ly` links; vary wording, typos, Hindi-English mix (Hinglish), Unicode tricks.
- [ ] Genuine templates: bank OTP/transaction alerts, delivery updates with real tracking links, telecom bills, OTT receipts, appointment reminders, friend chat messages containing real links.
- [ ] Add UCI SMS Spam Collection as an extra, with labels mapped.
- [ ] `data/benchmark/messages.csv`: `text,label,category,expected_verdict`.

**4. Files:** `data/benchmark/messages.csv`, `backend/scripts/gen_messages.py`.

**5. Guidance:** Genuine messages containing words like "OTP", "urgent", "account" are essential: they train you not to over-flag. Include >= 30 of them.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 1.2-T1 | Schema | csv exists | validate columns | pass | [ ] |
| 1.2-T2 | Category spread | csv | count by category | no scam category < 10 | [ ] |
| 1.2-T3 | Hard negatives | csv | count genuine messages with OTP/urgent/account words | >= 30 | [ ] |
| 1.2-T4 | Encoding | csv | load as UTF-8 incl. Devanagari and zero-width | loads without error | [ ] |
| 1.2-T5 | Leakage | csv | scam links must not reuse Phase 1.1 safe domains | none overlap | [ ] |

**7. Verification:** [ ] T1-T5 [ ] reviewed by a teammate.
**8. Completion:** message corpus frozen.

**9. Git**
```bash
git status
git add .
git commit -m "feat(benchmark): SMS corpus (scam and genuine, India-focused)"
git push origin main
```
**10. Rollback:** R2.

## Milestone 1.3 - QR and screenshot benchmark set

**1. Name:** Generated QR/screenshot samples.
**Depends on:** 1.1.

**2. Objective:** QR and screenshot images with known ground truth, produced by script.

**3. Tasks**
- [ ] `uv add --dev qrcode[pil]`; `scripts/gen_qr.py` creates PNGs for: valid UPI (`upi://pay?pa=name@oksbi&pn=...`), UPI with amount/collect pattern (scam), Spotify (`https://open.spotify.com/track/...`), fake Spotify lookalike, YouTube, Wi-Fi, vCard, `tel:`, `sms:`, mailto, crypto address, plain text, phishing URL, shortened URL, multi-QR image, rotated/blurred/low-contrast/small variants.
- [ ] `scripts/gen_screenshots.py` renders SMS-style screenshots (light and dark mode, different fonts and sizes) from `messages.csv` using Pillow.
- [ ] `data/benchmark/qr_manifest.csv` and `shots_manifest.csv`: `file,expected_payload_type,expected_verdict`.

**4. Files:** `scripts/gen_qr.py`, `scripts/gen_screenshots.py`, `data/benchmark/qr/*`, `data/benchmark/shots/*`, manifests.

**5. Guidance:** Also collect 5-10 real photos of QR codes (Google Pay merchant code, a printed Spotify code) from your own phones: synthetic QRs are cleaner than reality.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 1.3-T1 | Generation | scripts run | run both | files + manifests created | [ ] |
| 1.3-T2 | Decodability | qr set | decode with any phone camera (sample 10) | contents equal manifest | [ ] |
| 1.3-T3 | Variants exist | set | list | rotated, blurred, small, multi-QR present | [ ] |
| 1.3-T4 | Screenshot readability | shots | eyeball 5 | text legible | [ ] |
| 1.3-T5 | Size limit | all files | check sizes | each < 8 MB (API limit) | [ ] |

**7. Verification:** [ ] manifests complete [ ] real-photo samples included.
**8. Completion:** image corpus with ground truth.

**9. Git**
```bash
git status
git add .
git commit -m "feat(benchmark): QR and screenshot generators with manifests"
git push origin main
```
Not committed: personal photos with sensitive data (crop/blur or leave out).
**10. Rollback:** R2.

## Milestone 1.4 - Evaluation runner and quality gate

**1. Name:** One-command accuracy report.
**Depends on:** 1.1, 1.2, 1.3.

**2. Objective:** `uv run python scripts/evaluate.py` runs the engine on every benchmark file and prints metrics; it exits non-zero if gates fail.

**3. Tasks**
- [ ] Runner calls the real pipeline functions in-process (not HTTP) with a flag `--offline` (mocked network) and `--live`.
- [ ] Metrics: detection rate (recall on bad), false-positive rate (safe flagged SUSPICIOUS/DANGEROUS), precision, F1, confusion matrix, per-category breakdown, list of misclassified items, `COULD_NOT_VERIFY` count.
- [ ] Output `reports/eval-<date>.md` + JSON (git-ignored; one latest summary copied to `docs/eval-latest.md`).
- [ ] Gates (config constants): detection >= 90 %, FPR <= 3 %, overall >= 90 %.
- [ ] Run against the CURRENT engine to record the baseline numbers (expected to be poor; that is the point).

**4. Files:** `backend/scripts/evaluate.py`, `backend/app/eval/metrics.py`, `docs/eval-latest.md`.

**5. Guidance:** Treat `SUSPICIOUS` as "flagged" for detection and "wrong" for safe items; report it separately so you can tune.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 1.4-T1 | Metrics math | fixture of 4 known results | unit test | exact expected recall/FPR | [ ] |
| 1.4-T2 | Full run | corpora exist | run evaluate offline | report written | [ ] |
| 1.4-T3 | Gate fail | engine baseline | run | exit code 1, report lists failing gate | [ ] |
| 1.4-T4 | Empty input (edge) | empty csv | run | clear error, no crash | [ ] |
| 1.4-T5 | Per-item error | one item raises | run | item counted as error, run continues | [ ] |

**7. Verification:** [ ] baseline numbers saved in `docs/eval-latest.md` [ ] teammate reproduces them.
**8. Completion:** measurable baseline exists.

**9. Git**
```bash
git status
git add .
git commit -m "feat(eval): evaluation runner with quality gates and baseline report"
git push origin main
```
**10. Rollback:** R2.

## Phase 1 Completion Checkpoint
| Item | Record |
|---|---|
| Completed milestones | 1.1-1.4 |
| Tests passed | all `1.x-T*` |
| Known issues | (e.g. feed gaps, categories under-represented) |
| Git hash | (fill) |
| Overall verification | `evaluate.py` runs end-to-end and prints baseline |
| Go/No-Go | Go if baseline recorded; the gates are allowed to fail now |

```bash
git tag -a phase-1-done -m "Phase 1 complete" && git push origin main phase-1-done
```
