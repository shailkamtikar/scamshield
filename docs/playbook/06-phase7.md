# Phase 7 - API Hardening & Streaming

Branch: work directly on `main` (push after every verified milestone).

---

## Milestone 7.1 - Streaming progress (SSE) and API contract freeze

**1. Name:** Real, live scan progress.
**Depends on:** 5.3, 6.5.

**2. Objective:** The UI shows actual pipeline steps (extracting, resolving redirects, checking reputation...) instead of a fake spinner, and the final result schema is frozen for the frontend.

**3. Tasks**
- [ ] `POST /investigate/stream` (text), `/investigate/image/stream`, `/investigate/qr/stream` returning `text/event-stream` via FastAPI `StreamingResponse` (no extra dependency).
- [ ] Event types: `stage` (`{id, label, status: start|done|skipped|failed, detail}`), `partial` (`urls[]` verdicts as each completes), `verdict` (deterministic result, emitted *before* Gemini prose), `explanation`, `done` (full v2 JSON), `error`.
- [ ] Pipeline emits events through a callback/queue passed in the graph state; non-streaming endpoints keep working unchanged.
- [ ] Heartbeat comment every 15 s to survive proxies; client disconnect cancels work.
- [ ] Freeze schema in `docs/api.md` (`schema_version: 2`), export OpenAPI JSON for the frontend types.

**4. Files:** `app/api/stream.py`, `app/graph/events.py`, `app/graph/graph.py`, `docs/api.md`, `tests/test_stream.py`.

**5. Guidance:** SSE is chosen over WebSockets because it is one-way, works through Render's HTTP proxy, and is trivial in the browser (`fetch` + `ReadableStream`, needed anyway for POST bodies and file upload; `EventSource` only supports GET).

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 7.1-T1 | Event order | mocks | consume stream | `stage` events then `verdict` then `explanation` then `done` | [ ] |
| 7.1-T2 | Same result | mocks | compare `done` with non-stream response | identical JSON | [ ] |
| 7.1-T3 | Error mid-stream | provider raises | consume | `error` or `stage failed`, stream closes cleanly | [ ] |
| 7.1-T4 | Client disconnect | abort fetch | observe server | work cancelled, no leak | [ ] |
| 7.1-T5 | Heartbeat | slow step 30 s | consume | comments received | [ ] |
| 7.1-T6 | Regression | non-stream endpoints | call | unchanged | [ ] |
| 7.1-T7 | Image/QR stream | uploads | consume | stages for OCR/decoding appear | [ ] |

**7. Verification:** [ ] T1-T7 [ ] `curl -N` shows live events [ ] schema doc matches reality (validated by test against OpenAPI).
**8. Completion:** streaming + frozen contract.

**9. Git**
```bash
git status
git add .
git commit -m "feat(api): SSE progress streaming and frozen v2 contract"
git push origin main
```
**10. Rollback:** R2; non-stream endpoints unaffected.

---

## Milestone 7.2 - Abuse protection, error model, access control

**1. Name:** Safe to expose on the internet.
**Depends on:** 7.1.

**2. Objective:** Rate limiting, uniform errors, input limits, optional API key, locked-down CORS and headers.

**3. Tasks**
- [ ] `uv add slowapi` (per-IP rate limits e.g. 20/min and 200/day; needed because all external APIs and Gemini have free quotas that anonymous abuse would exhaust).
- [ ] Uniform error body `{error:{code,message,request_id}}`; global exception handler hides stack traces; every request gets an `X-Request-ID`.
- [ ] Input limits: message <= 5000 chars, URLs per request <= 6, upload <= 8 MB.
- [ ] Optional `X-API-Key` check if `API_ACCESS_KEY` set (so the demo can be public, a locked version available for the sponsor).
- [ ] Security headers middleware (`X-Content-Type-Options`, `Referrer-Policy`), CORS limited to `CORS_ORIGINS`, trusted-proxy handling for Render's client IP header.
- [ ] Structured JSON logging with redaction (no message contents beyond a hash/length, no keys).

**4. Files:** `app/main.py`, `app/api/errors.py`, `app/api/limits.py`, `app/logging.py`, `tests/test_security.py`.

**5. Guidance:** For authorization tests: the key is a shared secret, constant-time compare (`hmac.compare_digest`).

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 7.2-T1 | Rate limit | limit 20/min | 25 requests | 429 after 20, `Retry-After` set | [ ] |
| 7.2-T2 | API key required | `API_ACCESS_KEY` set | call without key | 401 | [ ] |
| 7.2-T3 | Wrong key | key set | wrong key | 401 (constant-time compare) | [ ] |
| 7.2-T4 | Valid key | key set | correct key | 200 | [ ] |
| 7.2-T5 | CORS | prod origins | request from evil origin | no CORS allow header | [ ] |
| 7.2-T6 | Error shape | force exception | call | uniform JSON, no traceback | [ ] |
| 7.2-T7 | Oversized text | 6000 chars | POST | 413/422 with code | [ ] |
| 7.2-T8 | Log hygiene | run requests | grep logs | no keys, no raw message text | [ ] |
| 7.2-T9 | Regression | full suite | pytest | green | [ ] |

**7. Verification:** [ ] T1-T9 [ ] manual `curl` abuse attempts fail.
**8. Completion:** public endpoint is quota-safe and leak-free.

**9. Git**
```bash
git status
git add .
git commit -m "security(api): rate limiting, uniform errors, optional API key, redacted logging"
git push origin main
```
**10. Rollback:** R2; remember rotating `API_ACCESS_KEY` in Render if it was exposed.

---

## Milestone 7.3 - Performance, caching, timeouts

**1. Name:** Fast enough for a live demo on free tiers.
**Depends on:** 7.2.

**2. Objective:** Predictable latency (<= 6 s typical text, <= 10 s worst case) and resilience to slow upstreams.

**3. Tasks**
- [ ] Global request deadline (e.g. 12 s): stages that miss it are marked `skipped(timeout)`, the engine returns with reduced confidence, never hangs.
- [ ] Parallelise per-URL and per-provider calls (`asyncio.gather` with per-task timeouts).
- [ ] In-memory TTL cache (24 h) for verdicts by canonical URL and for provider/RDAP responses; cache stats on `/health`.
- [ ] `/health` endpoint: ok, versions, which providers configured, Tranco/OpenPhish data age (uptime robot pings this).
- [ ] Memory guard: keep processes under ~400 MB (Render free 512 MB): lazy-load Tranco set, cap image dimensions, release OpenCV buffers.

**4. Files:** `app/engine/deadline.py`, `app/intel/cache.py`, `app/api/health.py`, `tests/test_perf.py`.

**5. Guidance:** Measure before optimising: add a timing stage list to logs.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 7.3-T1 | Slow provider | mock 30 s | POST | returns <= 12 s with provider skipped | [ ] |
| 7.3-T2 | Cache hit | same URL twice | POST | second < 0.5 s | [ ] |
| 7.3-T3 | Parallelism | 6 URLs each 2 s mock | POST | total < 5 s | [ ] |
| 7.3-T4 | Health | server up | GET `/health` | 200 with provider flags | [ ] |
| 7.3-T5 | Memory | 50 requests incl. images | observe RSS | < 400 MB | [ ] |
| 7.3-T6 | Confidence under timeout | skipped stage | POST | confidence lower and `missing` lists it | [ ] |

**7. Verification:** [ ] T1-T6 [ ] timing numbers recorded.
**8. Completion:** bounded latency, health endpoint ready for uptime monitoring.

**9. Git**
```bash
git status
git add .
git commit -m "perf(api): deadlines, parallel intel, caches and health endpoint"
git push origin main
```
**10. Rollback:** R2.

---

## Phase 7 Completion Checkpoint
| Item | Record |
|---|---|
| Completed milestones | 7.1-7.3 |
| Tests passed | all `7.x-T*` |
| Known issues | (fill) |
| Git hash | (fill) |
| Overall verification | full backend suite + evaluate.py gates still green |
| Go/No-Go | Go: backend feature-complete |

```bash
git tag -a phase-7-done -m "Phase 7 complete" && git push origin main phase-7-done
```
