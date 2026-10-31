# Phase 8 - Frontend Redesign

Work on `main` (push after every verified milestone). **Bar: it must look like a 10k-budget agency site, not template or AI-generic output.** References: the Lumen Hall screenshot the team shared and https://impeccable.style/neo-mirai/ (note: when fetched automatically that page exposed copy and image descriptions but no written design rules, so the team must open it in a browser and note specifics in `docs/design-references.md` before 8.1). Supporting libraries for craft: Motion (motion.dev), React Bits (animated text/background/spotlight components, copy-paste), 21st.dev (component patterns). Work from `frontend/` (React 19, Vite, Tailwind v4).

## Art direction (decided before any code)

What the Lumen Hall reference does, translated to ScamShield:
- **Borrow the motion and composition, not the colours.** The reference's golden tones belong to its own subject; ScamShield gets a palette made for cybersecurity + AI: a deep ink-navy/near-black base (`#07090F`), cool slate surfaces, one electric signature accent (cyan-teal `#22E3C4` or electric blue `#3D7BFF`, pick one in 8.1 and never mix both), and a restrained secondary used only for emphasis. Verdict colours stay semantic and are the only place warm colours appear: SAFE green `#2EE59D`, SUSPICIOUS amber `#FFB020`, DANGEROUS red `#FF4D5E`, COULD NOT VERIFY slate `#8A94A6`. On the result screen the scene's glow and gradient shift toward the verdict colour (like the reference's single-hue scenes) while the base stays dark.
- **Motion character (what to copy from the reference):** slow cinematic reveals, large type sliding/masking in line by line, hairline rules drawing in, a subtle parallax/scan-light over a full-bleed visual, and numbers counting up. Easing is smooth and deliberate (long ease-out, 600-900 ms for hero moments, 150-250 ms for UI feedback).
- **Massive condensed uppercase display type** (Anton, Bebas Neue or Big Shoulders Display via `@fontsource`) for headlines like "KNOW BEFORE YOU TAP." and the verdict word; **small mono/grotesk labels** for metadata (like ZONE 7, NOW, NEXT SHIFT in the reference).
- **A left data rail** with hairline dividers showing live facts (engine status, checks completed, response time, clock): always real values, never fake.
- **Hairline 1 px rules and outlined buttons with arrows**, near-zero corner radius, no drop-shadow cards, no glassmorphism.
- **Numbered editorial sections** (01 / 02 / 03) and a bottom strip of panels (here: the three input modes SMS / SCREENSHOT / QR, like the "halls" strip).
- **Cards that behave like instrument readouts** (OBSERVATION 21 / Crowd density / Medium) -> per-URL "INSPECTION 01" cards with fields Trust, Age, Redirects, Reputation.
- **Imagery:** one high-quality hero visual (WebGL/canvas shader such as a slow-moving network/grid/scan field, tinted by verdict) instead of stock illustrations; image budget < 300 kB, lazy loaded.

Anti-"AI-slop" review checklist for every UI milestone: no purple/blue gradient blobs; no centred hero + three identical icon cards; no emoji or icon-in-circle rows; no default Inter-on-white look; no uniform rounded-2xl card grid; no marketing filler copy; no motion without meaning; no fake statistics.

---

## Milestone 8.1 - Design system and tooling

**1. Name:** Tokens, fonts, motion primitives.
**Depends on:** 7.1 (API contract frozen).

**2. Objective:** One consistent visual language, dark theme default, reduced-motion respected.

**3. Tasks**
- [ ] `npm i motion` (animation library: layout transitions, springs, presence; justified vs. hand-written CSS for the verdict reveal, tab indicator and list orchestration). Import from `motion/react`.
- [ ] Self-hosted fonts via `@fontsource`: a condensed display face (Anton or Big Shoulders Display), a clean grotesk for body (Inter Tight or Geist) and a mono for labels (JetBrains Mono). No Google Fonts request.
- [ ] `npm i -D vitest @testing-library/react @testing-library/jest-dom jsdom` for component tests.
- [ ] Tokens in `src/index.css` (`@theme`): near-black base layers, hairline border colour, signature accent, the four semantic verdict colours and one signature accent, type scale with a very large display size (clamp 4rem-11rem), radius 0-4 px, 8-pt spacing rhythm, grid with a fixed left rail.
- [ ] Dark default, light retained via the existing toggle; persisted in `localStorage` with try/catch.
- [ ] `src/lib/motion.js`: shared springs/durations, `useReducedMotionSafe()` that disables transforms/parallax when `prefers-reduced-motion`.
- [ ] Remove unused starter assets (`vite.svg`).

**4. Files:** `package.json`, `src/index.css`, `src/lib/motion.js`, `src/main.jsx`, `src/context/ThemeContext.jsx`, `docs/design-references.md`.

**5. Guidance:** Keep the Material Symbols icon font? It loads from Google; replace with `lucide-react` (tree-shaken SVG icons) to improve performance and offline robustness. Decide once here and apply everywhere.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 8.1-T1 | Build | deps installed | `npm run build` | success, bundle size logged | [ ] |
| 8.1-T2 | Theme default | clear storage | load | dark | [ ] |
| 8.1-T3 | Theme toggle persists | toggle | reload | persisted; storage blocked -> still works | [ ] |
| 8.1-T4 | Reduced motion | OS setting on | load | animations disabled | [ ] |
| 8.1-T5 | Contrast | tokens | axe/Lighthouse | text contrast >= 4.5:1 on all verdict colours | [ ] |
| 8.1-T6 | Regression | old UI | submit text | still works | [ ] |

**7. Verification:** [ ] T1-T6 [ ] `npm run lint` clean.
**8. Completion:** foundation ready; no visible regressions.

**9. Git**
```bash
git status
git add .
git commit -m "feat(ui): design tokens, motion primitives, fonts, test tooling"
git push origin main
```
Not committed: `node_modules`, `dist`.
**10. Rollback:** R2; run `npm ci` after revert to restore `node_modules`.

---

## Milestone 8.2 - App shell, hero and ambient background

**1. Name:** First impression.
**Depends on:** 8.1.

**2. Objective:** A minimal, premium landing/shell with subtle ambient motion.

**3. Tasks**
- [ ] Header: logo, live "Engine online" status (calls `/health`), theme toggle; hides on scroll down / shows on scroll up (Motion `useScroll`).
- [ ] Hero: headline with animated gradient/blur-in text (React Bits-style text effect implemented locally; these are copy-paste components, no dependency), one-line value prop, three capability chips (SMS, Screenshot, QR).
- [ ] Ambient background: a single performant effect (soft aurora gradient or faint grid with spotlight following the cursor). Canvas/CSS only, paused when tab hidden and under reduced motion; target < 4 % CPU on a mid laptop.
- [ ] Footer with disclaimer and "how it works" link.
- [ ] Page-level `AnimatePresence` for idle -> scanning -> result transitions.

**4. Files:** `src/components/{Header,Hero,AmbientBackground,Footer}.jsx`, `src/App.jsx`.

**5. Guidance:** One ambient effect only; resist adding more. Lazy-load it so first paint isn't blocked.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 8.2-T1 | Render | dev server | open page | hero + header visible < 1 s | [ ] |
| 8.2-T2 | Backend offline | stop backend | load | header shows "Engine unreachable", form still usable | [ ] |
| 8.2-T3 | Reduced motion | OS flag | load | static gradient only | [ ] |
| 8.2-T4 | Perf | Lighthouse | run | Performance >= 90 desktop | [ ] |
| 8.2-T5 | Mobile 375 px | devtools | view | no horizontal scroll, readable | [ ] |
| 8.2-T6 | Background paused | switch tab | observe | animation loop stops | [ ] |

**7. Verification:** [ ] T1-T6 [ ] screenshot saved for the report.
**8. Completion:** polished shell.

**9. Git**
```bash
git status
git add .
git commit -m "feat(ui): animated hero, ambient background and shell"
git push origin main
```
**10. Rollback:** R2.

---

## Milestone 8.3 - Input experience (text, screenshot, QR)

**1. Name:** One beautiful input with three modes.
**Depends on:** 8.2.

**2. Objective:** Fast, obvious inputs: paste text, drop a screenshot, drop/scan a QR.

**3. Tasks**
- [ ] Segmented control with a sliding active pill (Motion `layoutId`) for SMS / Screenshot / QR.
- [ ] Text mode: auto-growing textarea, live character count, paste detection that highlights detected URLs inline, "Try an example" menu (scam SMS, genuine bank SMS, dead link, phishing URL) for demos.
- [ ] Image/QR dropzone: drag-over glow, instant thumbnail, remove button, paste-from-clipboard (Ctrl+V) support, client-side validation of type/size with friendly errors, animated "scan line" over the preview while uploading.
- [ ] Optional claimed organization field collapsed under "Add context".
- [ ] Keyboard: Ctrl/Cmd+Enter to analyse; full focus management and ARIA labels.
- [ ] Optional QR camera scan is out of scope for v1 (note in docs).

**4. Files:** `src/components/{ModeSwitch,TextInput,Dropzone,ExampleMenu,AnalyzeForm}.jsx`, `src/lib/validators.js`.

**5. Guidance:** Client validation is convenience only; the server stays authoritative.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 8.3-T1 | Mode switch | none | click each tab | pill animates, input swaps, state kept per mode | [ ] |
| 8.3-T2 | Empty submit | text empty | press analyse | button disabled | [ ] |
| 8.3-T3 | Example load | none | pick example | text + org filled | [ ] |
| 8.3-T4 | Wrong file type | drop `.pdf` | drop | error message, no upload | [ ] |
| 8.3-T5 | Oversize | 9 MB image | drop | error message | [ ] |
| 8.3-T6 | Clipboard paste | image in clipboard | Ctrl+V on page | thumbnail appears | [ ] |
| 8.3-T7 | Keyboard | tab order | navigate | logical order, visible focus, shortcut works | [ ] |
| 8.3-T8 | Component tests | vitest | `npm test` | pass | [ ] |

**7. Verification:** [ ] T1-T8 [ ] axe: zero critical issues.
**8. Completion:** all three inputs smooth and validated.

**9. Git**
```bash
git status
git add .
git commit -m "feat(ui): animated three-mode input with dropzone, paste and examples"
git push origin main
```
**10. Rollback:** R2.

---

## Milestone 8.3A - Live camera QR scanner (in-browser, nothing is opened)

**1. Name:** Scan a QR with the phone camera inside the web app.
**Depends on:** 8.3, 6.5 (`POST /investigate/qr-text`).

**2. Objective:** On a phone, the user taps "Scan QR", allows the camera, points at a QR code, and within a second ScamShield decodes it **in the browser** and sends only the decoded text to the backend for analysis. The QR destination is never opened on the user's device; the report says what the QR does and whether it is safe.

**3. Tasks**
- [ ] Camera access: `navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:"environment"},width:{ideal:1280}}})`. Requires HTTPS (Vercel provides it; `localhost` works in dev) and a user gesture to start (needed on iOS Safari; set `playsInline` and `muted` on the `<video>`).
- [ ] Decoding: use the native `BarcodeDetector` API where available (Chrome/Android); otherwise `npm i qr-scanner` (small, runs in a Web Worker, works on iOS Safari). Both are justified because iOS Safari has no `BarcodeDetector`. Scan frames via `requestAnimationFrame` throttled to ~15 fps.
- [ ] Permission UX: pre-prompt explanation ("Camera is used only to read the code on your device; video never leaves your phone"), clear states for `NotAllowedError` (how to re-enable in browser settings), `NotFoundError` (no camera), `NotReadableError` (camera busy), insecure context, and in-app browsers (Instagram/WhatsApp webviews often block the camera -> offer "Open in browser" or the upload fallback).
- [ ] Behaviour: reticle overlay with an animated scan line; on first valid code: `navigator.vibrate(30)` where supported, freeze frame, **stop all tracks** (`track.stop()`) so the camera light turns off, then call `/investigate/qr-text` with the decoded string and enter the normal scan timeline (8.4).
- [ ] Torch toggle where `track.getCapabilities().torch` exists; "Scan another" restarts; multiple codes in frame -> let the user pick which to analyse.
- [ ] **Safety rules:** decoded content is rendered as plain text (no `<a href>`, no auto-navigation, no `window.open`); URLs are shown defanged by default; a persistent banner reads "Link not opened - analysed remotely".
- [ ] Fallback: if camera or decoder is unavailable, switch to the image-upload mode with an explanation.
- [ ] Cleanup: stop the camera on unmount, on `visibilitychange` (tab hidden) and on mode change.

**4. Files:** `src/components/QrScanner.jsx`, `src/hooks/useCameraScanner.js`, `src/lib/qrDecode.js`, `src/components/AnalyzeForm.jsx`; backend `app/api/investigate_qr.py` (`/investigate/qr-text`, from 6.5).

**5. Guidance:** Decoding on-device is faster (no upload) and more private. The backend still does the deep inspection (redirect chain, reputation, page analysis) server-side, so the user's phone never touches the destination. Test on a real iPhone and a real Android phone; emulators do not prove camera behaviour.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 8.3A-T1 | Happy path (Android Chrome) | HTTPS deploy | tap Scan, allow, point at Spotify QR | decoded < 2 s, SAFE report, camera light off afterwards | [ ] |
| 8.3A-T2 | Happy path (iPhone Safari) | HTTPS | same | works via `qr-scanner` | [ ] |
| 8.3A-T3 | Permission denied | deny | tap Scan | clear help text, upload fallback offered | [ ] |
| 8.3A-T4 | No camera | desktop without webcam | tap Scan | friendly message, upload mode suggested | [ ] |
| 8.3A-T5 | Insecure context | plain HTTP over LAN | tap Scan | explains HTTPS requirement | [ ] |
| 8.3A-T6 | Phishing QR | phishing URL QR | scan | DANGEROUS, URL defanged, **no navigation** (check network tab; no tab opens) | [ ] |
| 8.3A-T7 | UPI QR | GPay QR on another screen | scan | payment card with payee/VPA/amount | [ ] |
| 8.3A-T8 | Tab hidden / unmount | switch tab or mode mid-scan | observe | camera tracks stopped | [ ] |
| 8.3A-T9 | Low light | dim room | toggle torch | works where supported, hidden otherwise | [ ] |
| 8.3A-T10 | No code for 30 s | none | wait | hint appears, no crash | [ ] |
| 8.3A-T11 | In-app browser | open link inside WhatsApp/Instagram | tap Scan | graceful fallback message | [ ] |
| 8.3A-T12 | Decoder unit test | frame fixtures | run vitest | known QR frames decode to expected strings | [ ] |

**7. Verification:** [ ] T1-T12 [ ] confirmed on at least one iPhone and one Android phone [ ] network tab shows the only outgoing call is to the ScamShield API with the decoded text, never to the QR's URL.
**8. Completion:** live scanning works on real phones, and a scanned link is never opened by the app.

**9. Git**
```bash
git status
git add .
git commit -m "feat(ui): live in-browser camera QR scanner with safe, non-navigating analysis"
git push origin main
```
Not committed: test photos of real QR codes containing private data.
**10. Rollback:** R2; upload mode remains as fallback.

---

## Milestone 8.4 - Live scan timeline (SSE client)

**1. Name:** Show real progress.
**Depends on:** 8.3, 7.1.

**2. Objective:** While analysing, the UI lists actual backend stages with animated state changes.

**3. Tasks**
- [ ] `src/lib/stream.js`: `fetch` POST + `ReadableStream` SSE parser (handles chunk boundaries, `\r\n`, heartbeat comments), abort on unmount/cancel.
- [ ] Reducer for stage events; timeline component: each step slides in, spinner -> check/skip/failed icon with spring, detail text (e.g. "Followed 3 redirects", "Domain registered 4 days ago").
- [ ] Early partial results: per-URL chips appear as soon as available; verdict card can appear before the explanation text streams in.
- [ ] Cancel button; timeout message after 25 s; automatic fallback to the non-stream endpoint if streaming fails.
- [ ] Error panel with retry and "backend asleep? retrying..." handling for Render cold start (retry with back-off, show friendly wake-up message).

**4. Files:** `src/lib/{stream,api}.js`, `src/components/{ScanTimeline,UrlChips}.jsx`, `src/hooks/useInvestigation.js`.

**5. Guidance:** All stage labels come from the backend event `label`, so the UI never lies about what is happening.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 8.4-T1 | SSE parser | split chunks fixture | feed | events parsed correctly | [ ] |
| 8.4-T2 | Happy path | live backend | analyse demo | timeline matches backend stages, final result shown | [ ] |
| 8.4-T3 | Cancel | during scan | click cancel | request aborted, UI idle | [ ] |
| 8.4-T4 | Stream failure | kill backend mid-scan | observe | falls back / error with retry | [ ] |
| 8.4-T5 | Cold start | backend asleep (or delayed 20 s) | analyse | wake-up message, eventual result | [ ] |
| 8.4-T6 | Skipped stage | provider missing | analyse | stage shown as skipped, not failed | [ ] |
| 8.4-T7 | Unmount | navigate away | observe | no state update warnings | [ ] |

**7. Verification:** [ ] T1-T7 [ ] verified on throttled "Slow 3G".
**8. Completion:** honest live progress.

**9. Git**
```bash
git status
git add .
git commit -m "feat(ui): SSE client and live scan timeline"
git push origin main
```
**10. Rollback:** R2; the non-stream path remains.

---

## Milestone 8.5 - Result report UI

**1. Name:** The verdict page.
**Depends on:** 8.4.

**2. Objective:** A result view that is instantly clear and richly explorable.

**3. Tasks**
- [ ] Verdict hero: big state (SAFE / SUSPICIOUS / DANGEROUS / COULD NOT VERIFY) with colour glow, count-up risk gauge (Motion `animate` on a number + SVG ring), confidence meter with tooltip showing `confidence_factors` ("based on 7 of 8 checks").
- [ ] "Why" section: decision path in plain words, signal chips grouped by Risk / Trust, each expandable with explanation.
- [ ] Per-URL cards: original -> final URL (with redirect chain visual), trust tier badge, domain age, certificate info, reputation providers as small status dots, page-inspection findings, copy-safe display (URLs shown defanged `hxxps://` by default with a "reveal" toggle - prevents accidental clicks).
- [ ] QR card: payload type, payee/VPA/amount for UPI, verified-service badge for Spotify etc.
- [ ] Image mode: preview next to extracted text with highlighted suspicious spans.
- [ ] Recommendation banner with actionable steps and India resources (report at cybercrime.gov.in, call 1930, block sender).
- [ ] Evidence accordion; Reasoning engine badge (Gemini model or "rules-only").
- [ ] Staggered entrance with `AnimatePresence`; layout-animated accordion; no animation longer than 600 ms.
- [ ] "Analyze another" resets with transition.

**4. Files:** `src/components/result/*`, `src/lib/risk.js` (new verdict config), `src/lib/format.js`.

**5. Guidance:** Colour is never the only signal (icon + label), for accessibility. Unknown fields must not crash the UI (defensive optional chaining; schema version check).

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 8.5-T1 | Each verdict | fixtures for 4 verdicts | render | correct colours/icons/text | [ ] |
| 8.5-T2 | UPI QR | fixture | render | payee/VPA/amount shown | [ ] |
| 8.5-T3 | Dead link | fixture | render | "link does not exist" message, not "safe" | [ ] |
| 8.5-T4 | Missing fields | partial JSON | render | no crash | [ ] |
| 8.5-T5 | Defang toggle | URL card | toggle | URL revealed/hidden | [ ] |
| 8.5-T6 | Unknown schema_version | version 99 | render | graceful notice | [ ] |
| 8.5-T7 | Visual regression | screenshots | compare | no unintended change | [ ] |
| 8.5-T8 | A11y | axe | run | no critical issues | [ ] |

**7. Verification:** [ ] T1-T8 [ ] demoed to a teammate unfamiliar with the project: they understand the verdict in < 5 s.
**8. Completion:** results are clear, honest and attractive.

**9. Git**
```bash
git status
git add .
git commit -m "feat(ui): verdict report with gauge, signals, URL/QR cards and recommendations"
git push origin main
```
**10. Rollback:** R2.

---

## Milestone 8.6 - PDF report v2, copy and share

**1. Name:** Exportable report.
**Depends on:** 8.5.

**2. Objective:** Print-friendly PDF and copyable summary reflecting the v2 data.

**3. Tasks**
- [ ] Update `src/lib/pdf.js` (jsPDF stays): verdict, score, confidence with factors, decision path, per-URL table (final URL defanged, trust tier, age, reputation), QR/UPI details, entities, signals, recommendation, methodology note + weights version, timestamp, disclaimer "automated assessment, not a guarantee".
- [ ] Multi-page layout reuse of existing helpers; black-on-white for printing.
- [ ] "Copy summary" and "Copy as JSON".
- [ ] Never include the raw uploaded image in the PDF unless the user opts in.

**4. Files:** `src/lib/pdf.js`, `src/components/result/Actions.jsx`.

**5. Guidance:** Generated entirely client-side; nothing stored.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 8.6-T1 | PDF generates | result fixture | click download | file saved, opens | [ ] |
| 8.6-T2 | Long evidence | 100 evidence lines | download | paginates, no overflow | [ ] |
| 8.6-T3 | Missing optional data | minimal result | download | no "undefined" text | [ ] |
| 8.6-T4 | Unicode | Hindi text in message | download | renders or degrades gracefully (document font limit) | [ ] |
| 8.6-T5 | Copy summary | click | clipboard has verdict + reasons | [ ] |

**7. Verification:** [ ] T1-T5 [ ] PDF printed in B&W is legible.
**8. Completion:** reports ready for the sponsor.

**9. Git**
```bash
git status
git add .
git commit -m "feat(ui): PDF report v2 and copy/export actions"
git push origin main
```
**10. Rollback:** R2.

---

## Milestone 8.7 - Responsive, accessibility and performance polish

**1. Name:** Production quality bar.
**Depends on:** 8.6.

**2. Objective:** Works on phones, keyboard, screen readers; fast.

**3. Tasks**
- [ ] Test widths 360 / 768 / 1280 / 1920; fix overflow.
- [ ] Keyboard-only run-through; skip link; focus rings; `aria-live` for scan status and verdict.
- [ ] Lighthouse: Performance >= 90, Accessibility >= 95, Best Practices >= 95; code-split `jspdf` (dynamic import on download click).
- [ ] 404 and error boundary page; empty-state and offline banner (`navigator.onLine`).
- [ ] Meta tags, favicon, OG image, `<title>`.

**4. Files:** `src/**`, `index.html`, `vite.config.js`.

**5. Guidance:** Offline behaviour: the app is online-only; show a clear banner and disable submit, retry on reconnect (test reconnect).

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 8.7-T1 | Mobile layout | 360 px | full flow | no overflow, tappable targets >= 44 px | [ ] |
| 8.7-T2 | Keyboard flow | none | analyse via keyboard only | works end-to-end | [ ] |
| 8.7-T3 | Screen reader | NVDA/VoiceOver quick check | analyse | verdict announced | [ ] |
| 8.7-T4 | Lighthouse | prod build preview | run | scores meet thresholds | [ ] |
| 8.7-T5 | Offline | disable network | submit | banner + disabled button; reconnect re-enables | [ ] |
| 8.7-T6 | Error boundary | throw in component | observe | friendly page | [ ] |
| 8.7-T7 | Bundle | build | inspect | main chunk < 250 kB gzip (jspdf lazy) | [ ] |

**7. Verification:** [ ] T1-T7 [ ] `npm run lint && npm test && npm run build` all green.
**8. Completion:** frontend release-quality.

**9. Git**
```bash
git status
git add .
git commit -m "polish(ui): responsive, a11y, performance and offline handling"
git push origin main
```
**10. Rollback:** R2.

---

## Phase 8 Completion Checkpoint
| Item | Record |
|---|---|
| Completed milestones | 8.1-8.7 |
| Tests passed | all `8.x-T*`, lint, build |
| Known issues | (fill) |
| Git hash | (fill) |
| Overall verification | full flow for text, screenshot and QR on dark/light, desktop/mobile |
| Go/No-Go | Go to deployment only if the three demo scenarios run flawlessly 3 times in a row |

```bash
git tag -a phase-8-done -m "Phase 8 complete" && git push origin main phase-8-done
```
