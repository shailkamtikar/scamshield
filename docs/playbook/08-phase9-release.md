# Phase 9 - Deployment, Documentation & Release

Branch: work directly on `main`. Targets: backend on Render (free web service, Docker), frontend on Vercel, uptime robot pinging `/health`. From the moment Render/Vercel are connected, every push to `main` auto-deploys, so run the full suite locally first.

---

## Milestone 9.1 - Backend container and Render service

> **KEY GATE C:** before starting, stop and ask the user to create Render, Vercel and UptimeRobot accounts per `KEYS.md` (Gate C).

**1. Name:** Reproducible backend deployment.
**Depends on:** 7.3, 5.1.

**2. Objective:** The backend runs in Docker with Tesseract (eng+hin) and builds its data files at image build time.

**3. Tasks**
- [ ] `backend/Dockerfile`: Python 3.12 slim, `apt-get install tesseract-ocr tesseract-ocr-eng tesseract-ocr-hin libgl1`(only if required by OpenCV headless), install `uv`, `uv sync --frozen --no-dev`, run `scripts/build_trust_data.py` (Tranco) and `scripts/train_lexical.py` at build, non-root user, `CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1`.
- [ ] `.dockerignore` (`.venv`, `tests`, `data/raw`, `.env`).
- [ ] `render.yaml` (Blueprint): service type web, Docker, health check path `/health`, env var declarations (values set in dashboard, `sync: false`).
- [ ] Env on Render: `GEMINI_API_KEY`, `SAFE_BROWSING_API_KEY`, `VIRUSTOTAL_API_KEY`, `URLHAUS_AUTH_KEY`, `CORS_ORIGINS=https://<vercel-domain>`, `API_ACCESS_KEY` (optional).
- [ ] Verify RAM stays under 512 MB (7.3-T5) inside the container; if not, reduce workers/lazy-load.
- [ ] Startup job: refresh OpenPhish feed in a background task (not blocking boot).

**4. Files:** `backend/Dockerfile`, `.dockerignore`, `render.yaml`, `backend/scripts/*`.

**5. Guidance:** One uvicorn worker: free tier has one shared CPU; in-memory caches are per process by design. The Render filesystem is ephemeral, so nothing persistent is needed (no database in v1). No secrets in the image; verify with `docker history`.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 9.1-T1 | Image builds | Docker installed | `docker build -t scamshield-api backend` | success | [ ] |
| 9.1-T2 | Runs locally | `docker run -p 8000:8000 --env-file backend/.env scamshield-api` | GET `/health` | 200 | [ ] |
| 9.1-T3 | OCR in container | T2 | POST screenshot | text extracted incl. Hindi sample | [ ] |
| 9.1-T4 | No secrets in image | built | `docker history`/grep for key prefix | none | [ ] |
| 9.1-T5 | Render deploy | repo connected | deploy via Blueprint | live URL, health green | [ ] |
| 9.1-T6 | Cold start | wait for sleep or restart | first request | responds within ~60 s then fast | [ ] |
| 9.1-T7 | CORS | prod origin set | browser request from Vercel preview | allowed; other origin blocked | [ ] |
| 9.1-T8 | Missing optional key | unset VT key in Render | request | works, coverage lower | [ ] |

**7. Verification:** [ ] T1-T8 [ ] memory graph in Render stays below limit under 20 requests.
**8. Completion:** public backend URL healthy.

**9. Git**
```bash
git status
git add .
git commit -m "build(deploy): Dockerfile, Render blueprint and data build steps"
git push origin main
```
Never commit: `.env`, Render env values.
**10. Rollback:** R2 for code; in Render use "Rollback to previous deploy" for the service. Rotate any key that was pasted into a build log.

---

## Milestone 9.2 - Frontend on Vercel and uptime monitor

**1. Name:** Public UI wired to the live API.
**Depends on:** 9.1, 8.7.

**2. Objective:** Deployed site, correct env, uptime robot, no cold-start surprises during the demo.

**3. Tasks**
- [ ] Vercel project with root directory `frontend`, build `npm run build`, output `dist`; env `VITE_API_BASE_URL=https://<render-url>`.
- [ ] `frontend/vercel.json` with SPA rewrite and security headers (CSP allowing only the API origin, `frame-ancestors 'none'`).
- [ ] Update Render `CORS_ORIGINS` with the final Vercel domain(s).
- [ ] UptimeRobot (free) HTTP monitor on `https://<render-url>/health` every 5 min (Render free sleeps after ~15 min idle).
- [ ] Demo-day checklist: ping health 5 minutes before, run all three demo inputs once to warm caches.

**4. Files:** `frontend/vercel.json`, `frontend/.env.example`, `docs/deploy.md`.

**5. Guidance:** Vite env vars are public at build time - never put secrets in `VITE_*`. Provider keys stay on Render only.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 9.2-T1 | Production load | deployed | open URL | loads, "Engine online" | [ ] |
| 9.2-T2 | Text scan | deployed | demo scam | DANGEROUS | [ ] |
| 9.2-T3 | Screenshot scan | deployed | upload | result | [ ] |
| 9.2-T4 | QR scan | deployed | GPay + Spotify QRs | SAFE | [ ] |
| 9.2-T5 | Deep link refresh | deployed | reload on any route | no 404 (SPA rewrite) | [ ] |
| 9.2-T6 | CSP | deployed | devtools console | no violations in normal use | [ ] |
| 9.2-T7 | Uptime | monitor 24 h | check dashboard | no sleeping, no downtime | [ ] |
| 9.2-T8 | Mobile device | real phone | full flow | works | [ ] |

**7. Verification:** [ ] T1-T8 [ ] bundle contains no secret (`grep dist` for key prefixes).
**8. Completion:** public URL ready for sponsor.

**9. Git**
```bash
git status
git add .
git commit -m "build(deploy): Vercel config, CSP headers and deployment docs"
git push origin main
```
**10. Rollback:** Vercel "Instant Rollback" to the previous deployment; R2 for code.

---

## Milestone 9.3 - Full acceptance run on the deployed system

**1. Name:** Prove the numbers on production.
**Depends on:** 9.2.

**2. Objective:** Final accuracy evidence and an acceptance script for the sponsor.

**3. Tasks**
- [ ] `evaluate.py --target https://<render-url>` using HTTP (respecting rate limits via a temporary key or throttle).
- [ ] Fresh batch of today's live phishing URLs (not used in tuning) + 100 safe real-world links across categories (banks, govt, shopping, travel, OTT...), report detection and FPR.
- [ ] Sponsor scenario checklist: a stupid link -> flagged; real bank address -> not flagged; GPay QR -> safe; Spotify QR -> safe; phishing QR -> flagged; dead-but-legit-looking link -> could-not-verify; gibberish domain -> unsafe.
- [ ] Record screenshots and the evaluation report in `docs/acceptance-report.md`.

**4. Files:** `docs/acceptance-report.md`, `backend/scripts/evaluate.py`.

**5. Guidance:** Report honestly where it fails and why; a documented limitation is better than a hidden one in front of a panel.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 9.3-T1 | Detection | fresh phishing batch | evaluate | >= 85-90 % | [ ] |
| 9.3-T2 | FPR | 100 safe links | evaluate | <= 3 % | [ ] |
| 9.3-T3 | Sponsor scenarios | 7 scenarios | run manually | 7/7 as described | [ ] |
| 9.3-T4 | Latency | 50 requests | measure | p95 < 10 s | [ ] |
| 9.3-T5 | Failure drill | disable a provider key | run | still answers | [ ] |

**7. Verification:** [ ] T1-T5 [ ] report committed.
**8. Completion:** measured, documented acceptance.

**9. Git**
```bash
git status
git add .
git commit -m "docs(acceptance): production evaluation report and sponsor scenarios"
git push origin main
```
**10. Rollback:** documentation only; R2.

---

## Milestone 9.4 - Documentation and repository cleanliness

**1. Name:** Handover-ready repo.
**Depends on:** 9.3.

**2. Objective:** Anyone can understand, run, extend and defend the project.

**3. Tasks**
- [ ] Root `README.md` (currently empty): what it is, screenshots/GIF, architecture diagram, features, quick start, env variables table, deployment, limitations, accuracy numbers.
- [ ] `docs/architecture.md` (pipeline diagram, signal/verdict/confidence formulas, weights version), `docs/api.md`, `docs/deploy.md`, `docs/limitations.md` (cloaked phishing, new domains, quota limits, OCR limits), `docs/extending-trust-registry.md`.
- [ ] `LICENSE`, `.env.example` complete, `CONTRIBUTING`-style note (team only).
- [ ] Remove dead code and stray files (`frontend/dist` untracked, old scripts), final `uv run pytest`, `npm run lint && npm test && npm run build`.
- [ ] Final co-author audit and secret scan across **full history**: `git log -p | grep -iE "AIza|api[_-]?key"` (investigate any hit; rotate keys).

**4. Files:** `README.md`, `docs/*`, `LICENSE`.

**5. Guidance:** Judging panels read the README first; make the first screen impressive and honest.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 9.4-T1 | Fresh clone | new folder | follow README only | app runs locally in < 15 min | [ ] |
| 9.4-T2 | Links | docs | check markdown links | none broken | [ ] |
| 9.4-T3 | History secrets | repo | secret scan | clean | [ ] |
| 9.4-T4 | Contributors | repo | `git shortlog -sne --all` + GitHub contributors page | only the team | [ ] |
| 9.4-T5 | CI | push | Actions | green | [ ] |

**7. Verification:** [ ] T1-T5.
**8. Completion:** release candidate.

**9. Git**
```bash
git status
git add .
git commit -m "docs: README, architecture, API, deployment and limitations"
git push origin main
```
**10. Rollback:** R2.

---

## Phase 9 Completion Checkpoint
| Item | Record |
|---|---|
| Completed milestones | 9.1-9.4 |
| Tests passed | all `9.x-T*` |
| Known issues | (fill) |
| Git hash | (fill) |
| Overall verification | live URL passes acceptance scenarios; CI green |
| Go/No-Go | Go = release |

```bash
git tag -a v1.0.0 -m "ScamShield v1.0.0" && git push origin main v1.0.0
```

---

# Final Release Checklist

**Functionality**
- [ ] Text, screenshot and QR inputs all return v2 results through the deployed UI
- [ ] Gibberish/fake domain -> DANGEROUS; genuine bank/official site -> SAFE; dead-but-legit-looking -> COULD_NOT_VERIFY
- [ ] GPay/UPI and Spotify QRs verified safe; phishing QR flagged; QR contents investigated
- [ ] Confidence and score are deterministic and explainable (`decision_path`, `confidence_factors`)
- [ ] PDF/summary export works

**Testing**
- [ ] Backend `uv run pytest -m "not live"` green; coverage recorded
- [ ] Frontend lint, tests, build green
- [ ] `evaluate.py` gates met (detection >= 90 %, FPR <= 3 %, overall >= 90 %; floor 85 %)
- [ ] Live acceptance run documented in `docs/acceptance-report.md`

**Security**
- [ ] No client-supplied file paths; uploads validated by magic bytes, size, dimensions
- [ ] SSRF guard tests green; resolver never reaches private ranges
- [ ] Rate limiting, uniform errors, redacted logs, restricted CORS, security headers
- [ ] No secrets in repo history, Docker image or frontend bundle; keys only in Render env
- [ ] Prompt-injection tests green (Gemini cannot change verdict)

**Performance**
- [ ] p95 latency < 10 s; typical text scan <= 6 s
- [ ] Memory < 400 MB on Render; uptime monitor green for 24 h
- [ ] Lighthouse Performance >= 90, Accessibility >= 95

**Deployment**
- [ ] Render service healthy, Vercel production deploy, CORS correct
- [ ] Rollback paths tested once (Render + Vercel)
- [ ] Provider failure drill passed

**Documentation**
- [ ] README, architecture, API, deploy, limitations, trust-registry guide
- [ ] Evaluation numbers and methodology included, with honest limitations

**Git repository cleanliness**
- [ ] `git status` clean, on `main`, tag `v1.0.0` pushed
- [ ] Only the team appears as author/contributor (no `Co-Authored-By`, no extra collaborators)
- [ ] `.gitignore` covers `.env`, `node_modules`, `dist`, `.venv`, `data/raw`, caches
- [ ] Phase tags `phase-0-done` ... `phase-8-done` exist as recovery points
