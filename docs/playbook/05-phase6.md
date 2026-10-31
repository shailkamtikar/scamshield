# Phase 6 - QR Pipeline

Branch: work directly on `main` (push after every verified milestone).

Key principle: **QR = decode -> classify payload type -> type-specific checks -> (URLs go through Phase 2/3)**. A UPI QR is "format-valid payment", which is *not* the same as "the payee is trustworthy"; the report shows payee and amount for user confirmation.

---

## Milestone 6.1 - Robust QR decoder

**1. Name:** Decode what OpenCV alone misses.
**Depends on:** 4.3.

**2. Objective:** Read rotated, small, blurry, low-contrast, multiple and phone-photographed QR codes.

**3. Tasks**
- [ ] `uv add zxing-cpp` (fast, accurate multi-code reader with prebuilt wheels; chosen over `pyzbar` to avoid a system `libzbar` dependency on Render).
- [ ] Decode pipeline: zxing-cpp on the original -> on grayscale/upscaled -> on contrast-enhanced / thresholded variants -> on rotations -> OpenCV `QRCodeDetector` and `QRCodeDetectorAruco` fallbacks.
- [ ] Return a list of `DecodedCode{text, bytes, format, position}` (multi-QR support).
- [ ] Reject non-QR barcodes explicitly (report format) but allow EAN etc. as `UNSUPPORTED_BARCODE`.

**4. Files:** `app/services/qr.py`, `tests/test_qr_decode.py`.

**5. Guidance:** Real-photo samples from 1.3 are the true test; synthetic ones are too easy.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 6.1-T1 | Clean QR | generated | decode | text equals ground truth | [ ] |
| 6.1-T2 | Rotated 30/90/180 | variants | decode | all decode | [ ] |
| 6.1-T3 | Blurred/low-contrast | variants | decode | >= 90 % decode | [ ] |
| 6.1-T4 | Two QRs in one image | multi sample | decode | 2 results | [ ] |
| 6.1-T5 | No QR | photo of a cat | decode | empty list | [ ] |
| 6.1-T6 | Real photos | 5-10 real samples | decode | >= 80 % decode | [ ] |
| 6.1-T7 | Corrupt image | random bytes | decode | clean error | [ ] |
| 6.1-T8 | Large image 6000 px | generated | decode | < 3 s | [ ] |

**7. Verification:** [ ] T1-T8 [ ] decode rate on the QR manifest reported (target >= 95 % synthetic, >= 80 % real).
**8. Completion:** decoder reliable enough that failures are the image's fault.

**9. Git**
```bash
git status
git add .
git commit -m "feat(qr): multi-strategy decoder with zxing-cpp and OpenCV fallbacks"
git push origin main
```
**10. Rollback:** R2 (reverts the dependency too; run `uv sync`).

---

## Milestone 6.2 - Payload classifier and parsers

**1. Name:** Know what the QR contains.
**Depends on:** 6.1.

**2. Objective:** Turn the raw string into a typed object.

**3. Tasks**
- [ ] `app/qr/payload.py` with parsers for: `URL` (http/https and scheme-less), `UPI` (`upi://pay?pa=&pn=&am=&cu=&tn=&mc=&tr=`), `WIFI` (`WIFI:T:WPA;S:...;P:...;;`), `VCARD`/`MECARD`, `TEL`, `SMS`/`SMSTO`, `MAILTO`, `GEO`, `CRYPTO` (bitcoin:, ethereum:), `EVENT`, `APP_DEEPLINK` (e.g. `spotify:track:...`, `intent://`, `market://`, `itms-apps://`), `TEXT`, `UNKNOWN`.
- [ ] Generic `data:`/`javascript:`/`file:` payloads are classified `DANGEROUS_SCHEME`.
- [ ] Each payload includes `parsed` fields and `raw`; classification is deterministic and total (never raises).
- [ ] Android `intent://` and APK links flagged (`APK_OR_INTENT`).

**4. Files:** `app/qr/payload.py`, `app/qr/__init__.py`, `tests/test_qr_payload.py`.

**5. Guidance:** Pure parsing, no network. Keep strict parsing of query strings using `urllib.parse` (no regex hacks) so tricky encodings (`%40`) work.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 6.2-T1 | UPI | `upi://pay?pa=shop@oksbi&pn=Shop&am=100&cu=INR` | classify | UPI, fields parsed | [ ] |
| 6.2-T2 | URL | `https://open.spotify.com/track/xyz` | classify | URL | [ ] |
| 6.2-T3 | Spotify URI | `spotify:track:abc` | classify | APP_DEEPLINK(spotify) | [ ] |
| 6.2-T4 | Wi-Fi | `WIFI:T:WPA;S:Cafe;P:pass;;` | classify | WIFI | [ ] |
| 6.2-T5 | Dangerous | `javascript:alert(1)` | classify | DANGEROUS_SCHEME | [ ] |
| 6.2-T6 | Malformed UPI | `upi://pay?pa=` | classify | UPI with `invalid` flag, no exception | [ ] |
| 6.2-T7 | Bare domain | `sbi.co.in/login` | classify | URL | [ ] |
| 6.2-T8 | Fuzz | 5000 random strings | classify | never raises | [ ] |

**7. Verification:** [ ] T1-T8 [ ] every type in the manifest classified correctly.
**8. Completion:** deterministic typed payloads.

**9. Git**
```bash
git status
git add .
git commit -m "feat(qr): payload classifier and parsers (UPI, URL, Wi-Fi, vCard, deeplinks, etc.)"
git push origin main
```
**10. Rollback:** R2.

---

## Milestone 6.3 - UPI payment QR analyser

**1. Name:** Google Pay / PhonePe / Paytm / BHIM QR handling.
**Depends on:** 6.2, 2.6.

**2. Objective:** A genuine merchant/personal UPI QR is reported as a valid payment QR and not flagged; scam patterns are flagged.

**3. Tasks**
- [ ] `data/upi_handles.json`: PSP handles from NPCI's published list (e.g. `oksbi, okhdfcbank, okicici, okaxis, ybl, ibl, axl, paytm, apl, upi, sbi, hdfcbank, icici, axisbank, ...`). Verify the list against the current NPCI document when implementing.
- [ ] Validate VPA format `name@handle`, handle known; unknown handle = `UPI_UNKNOWN_HANDLE`.
- [ ] Payee name `pn` vs VPA plausibility (e.g. name "SBI Customer Care" on a personal-looking VPA with random digits) = signal; payee claiming a known brand (registry) on a VPA that isn't that brand's = `UPI_BRAND_PAYEE_MISMATCH`.
- [ ] Amount logic: scanning a QR **to pay** with large `am` is normal for merchants; the scam pattern is "scan this QR to **receive** money" (marketplace/OLX/refund scams): trigger when the QR carries a pre-filled amount and the surrounding context (if image text/OCR or `claimed_organization` implies "refund/prize/receive") says receive; otherwise show an informational `PAYMENT_REQUEST` with payee and amount and the warning "Scanning pays money out; you never need to scan a QR or enter a PIN to receive money."
- [ ] Include `mc` merchant category code (merchant QRs) as a positive signal when present with a known handle.
- [ ] Output a `qr_summary` card: payee name, VPA, amount, currency, note, merchant code.
- [ ] Verdict mapping: well-formed UPI with known handle and no risk signals = `SAFE` with `kind: payment_qr` and a payee-confirmation note; any risk signal -> SUSPICIOUS/DANGEROUS.

**4. Files:** `app/qr/upi.py`, `data/upi_handles.json`, `tests/test_upi.py`.

**5. Guidance:** Honest wording: "This is a valid UPI payment QR. Verify the payee name before paying." We cannot verify real-world ownership of a VPA offline; do not claim more.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 6.3-T1 | Genuine Google Pay merchant QR | real/synthetic `pa=store@okaxis&pn=Store&mc=5411` | analyse | SAFE payment QR with summary | [ ] |
| 6.3-T2 | Unknown handle | `pa=x@fakebank99` | analyse | `UPI_UNKNOWN_HANDLE`, SUSPICIOUS | [ ] |
| 6.3-T3 | Brand payee mismatch | `pn=SBI Refund Dept&pa=9812345678@ybl` | analyse | `UPI_BRAND_PAYEE_MISMATCH` | [ ] |
| 6.3-T4 | Receive-money scam | image text "scan to receive Rs 5000" + UPI QR | analyse | DANGEROUS/SUSPICIOUS with receive-money warning | [ ] |
| 6.3-T5 | Invalid VPA | `pa=abc` | analyse | malformed flag | [ ] |
| 6.3-T6 | Zero amount personal QR | `pa=friend@okicici` no `am` | analyse | SAFE | [ ] |
| 6.3-T7 | Regression | non-UPI QR | analyse | UPI analyser not invoked | [ ] |
| 6.3-T8 | Benchmark | UPI subset of manifest | evaluate | no genuine UPI marked unsafe | [ ] |

**7. Verification:** [ ] T1-T8 [ ] test with a real GPay/PhonePe QR on your phones.
**8. Completion:** valid payment QRs not falsely flagged; common QR scams flagged.

**9. Git**
```bash
git status
git add .
git commit -m "feat(qr): UPI payment QR analyser with handle validation and scam heuristics"
git push origin main
```
**10. Rollback:** R2.

---

## Milestone 6.4 - Known-service verification and QR URL investigation

**1. Name:** Spotify and friends verified; every URL inside QR goes through the full engine.
**Depends on:** 6.2, Phase 3.

**2. Objective:** A Spotify QR is verified safe because its URL belongs to Spotify; a QR pointing at an unknown site gets the complete Phase 2/3 treatment (redirects, reputation, page).

**3. Tasks**
- [ ] `app/qr/services.py`: map official domains/schemes from the trust registry (2.6) to "services" (Spotify, YouTube, JioSaavn, Instagram, WhatsApp `wa.me`, Telegram `t.me`, LinkedIn, Play Store/App Store, Zoom, Google Maps, Razorpay payment links, IRCTC, etc.) so the card reads "Spotify track link (verified Spotify domain)".
- [ ] Exact registrable-domain matching only; `open.spotify.com.evil.tk` fails.
- [ ] Shortener/redirect QR (`spotify.link`, `bit.ly`) -> resolver follows to final; if final host is the service -> verified.
- [ ] Non-service URL -> full URL pipeline; result merged into the QR response.
- [ ] Deeplinks (`spotify:`) verified by scheme registry; `intent://`/APK -> risk signal.
- [ ] Wi-Fi: flag `WPA`-less open networks as informational; vCard/tel/sms: show content and flag premium-rate/shortcode SMS patterns; crypto: always `SUSPICIOUS` informational "irreversible payments" unless context says otherwise.

**4. Files:** `app/qr/services.py`, `app/qr/analyze.py`, `tests/test_qr_services.py`.

**5. Guidance:** This is where "the stuff inside the QR" is actually investigated: the QR layer adds no scoring of its own for URLs; it delegates to the same engine so QR and text give identical verdicts for identical URLs (cross-modal consistency, tested).

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 6.4-T1 | Spotify track | URL QR | analyse | SAFE, service=Spotify, verified domain | [ ] |
| 6.4-T2 | Lookalike Spotify | `open.spotify.com.evil.tk` | analyse | DANGEROUS | [ ] |
| 6.4-T3 | spotify.link redirect | respx to open.spotify.com | analyse | SAFE | [ ] |
| 6.4-T4 | Phishing URL QR | feed URL (mock) | analyse | DANGEROUS with reputation evidence | [ ] |
| 6.4-T5 | Consistency | same URL as text and as QR | compare | identical verdict and score | [ ] |
| 6.4-T6 | Intent/APK | `intent://...` | analyse | risk signal | [ ] |
| 6.4-T7 | Unknown but clean new site | respx clean | analyse | SUSPICIOUS (low) not SAFE | [ ] |
| 6.4-T8 | Dead URL in QR | NXDOMAIN legit-looking | analyse | COULD_NOT_VERIFY | [ ] |

**7. Verification:** [ ] T1-T8 [ ] cross-modal consistency test added to the permanent suite.
**8. Completion:** QR contents investigated by the same engine.

**9. Git**
```bash
git status
git add .
git commit -m "feat(qr): known-service verification and full URL investigation of QR payloads"
git push origin main
```
**10. Rollback:** R2.

---

## Milestone 6.5 - QR endpoint integration

**1. Name:** `/investigate/qr` on engine v2.
**Depends on:** 6.1-6.4, 5.3 (shared upload validation).

**2. Objective:** One endpoint returning the v2 response + QR-specific section.

**3. Tasks**
- [ ] Use shared `uploads.py` validation (magic bytes, size, dimensions).
- [ ] For multi-QR images analyse each (cap 5), overall verdict = worst; response `qr_codes: [{payload_type, summary, verdict, ...}]`.
- [ ] Errors: no QR found -> 422 `QR_NOT_FOUND`; unsupported barcode -> 422 `UNSUPPORTED_BARCODE`.
- [ ] **Required** endpoint `POST /investigate/qr-text` accepting `{text}` (the decoded QR content): used by the live camera scanner (8.3A), by tests, and by paste-in demos. Same validation, same engine, same response as the image endpoint. The backend never returns or follows anything to the user's device.

**4. Files:** `app/api/investigate_qr.py`, `app/models/response.py`, `tests/test_api_qr.py`.

**5. Guidance:** Keep `decoded_text` in the response (legacy frontend key).

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 6.5-T1 | GPay QR image | generated | POST | SAFE, payment card | [ ] |
| 6.5-T2 | Spotify QR image | generated | POST | SAFE, Spotify card | [ ] |
| 6.5-T3 | Phishing QR image | generated | POST | DANGEROUS | [ ] |
| 6.5-T4 | No QR | cat photo | POST | 422 QR_NOT_FOUND | [ ] |
| 6.5-T5 | Multi-QR with one bad | generated | POST | overall DANGEROUS, both listed | [ ] |
| 6.5-T6 | Upload attacks | exe-as-png, bomb, 9 MB | POST | 415/413/422 | [ ] |
| 6.5-T7 | Benchmark | QR manifest | evaluate | >= 90 % correct, **0 genuine payment/Spotify QRs flagged unsafe** | [ ] |
| 6.5-T8 | Legacy UI | old frontend | scan QR | still renders | [ ] |

**7. Verification:** [ ] T1-T8 [ ] manual test with your phone-screen QR photos.
**8. Completion:** all three inputs run on engine v2.

**9. Git**
```bash
git status
git add .
git commit -m "feat(api): QR endpoint on engine v2 with multi-QR support"
git push origin main
```
**10. Rollback:** R2.

---

## Phase 6 Completion Checkpoint
| Item | Record |
|---|---|
| Completed milestones | 6.1-6.5 |
| Tests passed | all `6.x-T*` |
| Known issues | (fill) |
| Git hash | (fill) |
| Overall verification | QR manifest gates met; cross-modal consistency green |
| Go/No-Go | Go to Phase 7 only if no genuine GPay/Spotify QR is flagged |

```bash
git tag -a phase-6-done -m "Phase 6 complete" && git push origin main phase-6-done
```
