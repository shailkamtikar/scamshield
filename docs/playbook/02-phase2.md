# Phase 2 - URL Intelligence Core

Branch: work directly on `main` (push after every verified milestone).

Common design: new package `backend/app/intel/`, each module exposes a pure function returning a dataclass `Finding(id, status, points_hint, detail, source)`. Network calls use `httpx` (explicit timeouts, one shared client); tests mock it with `respx`.

---

## Milestone 2.1 - URL extraction and canonical normalization

**1. Name:** Find every URL (including scheme-less) and canonicalise it.
**Depends on:** Phase 1.

**2. Objective:** Catch `bit.ly/x`, `paypal-help.com/login`, `www.sbi.co.in`, `HXXP://`, defanged `hxxps://evil[.]com`, URLs in Hindi text, and detect invisible/Unicode tricks (your "ASCII characters" requirement).

**3. Tasks**
- [ ] `uv add tldextract idna confusable-homoglyphs`.
- [ ] `app/intel/urls.py`: extraction regex for scheme and scheme-less domains (validate TLD against the public suffix list to avoid matching "e.g." or "file.txt"), refang `[.]`, `hxxp`, strip trailing punctuation and wrapping brackets.
- [ ] Canonical form: lowercase host, IDNA/punycode decode, remove default ports, strip `www.`, keep path/query separately, expose `registrable_domain`, `subdomain`, `tld`.
- [ ] Unicode report: flag mixed-script labels, confusable characters, zero-width/bidi control chars, `xn--` labels with their decoded form, userinfo trick (`https://sbi.co.in@evil.com`), non-ASCII anywhere in host.
- [ ] Replace `extraction_node` and `normalize_url` usage; keep the old regex as a regression oracle in tests.
- [ ] Hand off a `ParsedUrl` object (not a string) downstream.

**4. Files:** `app/intel/__init__.py`, `app/intel/urls.py`, `app/graph/nodes/extraction.py`, `app/services/url_normalize.py` (thin wrapper), `tests/test_urls.py`.

**5. Guidance:** `tldextract` is used offline (`suffix_list_urls=()` with the bundled snapshot) so runtime never blocks on a download. `confusable-homoglyphs` avoids hand-maintaining Unicode confusable tables.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 2.1-T1 | Scheme-less | none | extract from "visit sbi-kyc-update.com/login now" | 1 URL, host `sbi-kyc-update.com` | [ ] |
| 2.1-T2 | Defanged | none | "hxxps://evil[.]com/a" | refanged `https://evil.com/a` | [ ] |
| 2.1-T3 | Homoglyph | none | `https://аpple.com` (Cyrillic a) | flag mixed-script + confusable | [ ] |
| 2.1-T4 | Userinfo trick | none | `https://sbi.co.in@evil.com` | host=`evil.com`, flag deceptive userinfo | [ ] |
| 2.1-T5 | Zero-width char | none | `pay​tm.com` | flag invisible char | [ ] |
| 2.1-T6 | False-match guard | none | "e.g. file.txt and v1.2.3" | 0 URLs | [ ] |
| 2.1-T7 | Regression | old tests | duplicate URL twice | deduped to one | [ ] |
| 2.1-T8 | Edge: huge text | 1 MB text | extract | < 1 s, no catastrophic regex backtracking | [ ] |

**7. Verification:** [ ] T1-T8 [ ] no regex timeouts [ ] graph still runs (Phase 0 tests green).
**8. Completion:** one trusted URL parser feeding everything.

**9. Git**
```bash
git status
git add .
git commit -m "feat(intel): robust URL extraction, canonicalisation and Unicode deception detection"
git push origin main
```
**10. Rollback:** R2; revert also removes the 3 added dependencies from `pyproject.toml`/`uv.lock` (run `uv sync`).

---

## Milestone 2.2 - Lexical and lookalike analysis (offline)

**1. Name:** Detect fake-looking domains without touching the network.
**Depends on:** 2.1.

**2. Objective:** Gibberish domains (`xkqzjw7.top`), brand lookalikes (`hdfcbank-secure.in`, `amaz0n-offers.com`), suspicious TLDs, excessive hyphens/digits, long random subdomains are caught instantly; legitimate unusual names are not.

**3. Tasks**
- [ ] Gibberish scorer: character-bigram/trigram language model trained once from Tranco top domains' labels (`scripts/train_lexical.py` -> `app/intel/data/lexical_model.json`, a few hundred KB), plus entropy, vowel/consonant ratio, digit ratio, length.
- [ ] Brand-lookalike detector: compare each domain label against a protected brand list (built in 2.6; for now a seed of 300 global+Indian brands) using Damerau-Levenshtein/rapidfuzz, homoglyph substitution (`0->o`, `1->l`), and compound detection (`brand-` + admin word). Output matched brand + similarity.
- [ ] Replace the substring keyword rule ("account", "update" anywhere in URL) with context-aware rules: keywords only count on a domain that is not on the trusted registry (so `sbi.co.in/login` is never penalised).
- [ ] Risky TLD list (`.top`, `.xyz`, `.click`, `.live`, `.icu`, `.cfd`, ...) as a weak signal only.
- [ ] Output signals: `DOMAIN_GIBBERISH`, `BRAND_LOOKALIKE`, `COMBOSQUAT`, `RISKY_TLD`, `HOMOGRAPH`, `RAW_IP`, `DEEP_SUBDOMAINS`.

**4. Files:** `app/intel/lexical.py`, `app/intel/brands_seed.json`, `scripts/train_lexical.py`, `app/graph/nodes/url_investigation.py` (calls intel), `tests/test_lexical.py`.

**5. Guidance:** A small n-gram model is chosen over an ML library to keep the Render image small and the result explainable ("bigram 'qz' never appears in real domains"). Calibrate the gibberish threshold on the Phase 1 safe set so real short brand names (`ola`, `zee5`, `paytm`) are not flagged.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 2.2-T1 | Gibberish | model trained | `xkqzjw7vp.top` | `DOMAIN_GIBBERISH` | [ ] |
| 2.2-T2 | Real short brand | model trained | `paytm.com`, `zee5.com`, `ola.in` | no gibberish flag | [ ] |
| 2.2-T3 | Lookalike | brand seed | `hdfcbank-secure.in` | `BRAND_LOOKALIKE`(HDFC) + COMBOSQUAT | [ ] |
| 2.2-T4 | Digit swap | brand seed | `amaz0n.in` | lookalike of Amazon | [ ] |
| 2.2-T5 | Trusted login page | none | `https://www.sbi.co.in/login` | no keyword penalty | [ ] |
| 2.2-T6 | FPR check | Phase 1 safe set | run lexical only over safe URLs | < 2 % flagged | [ ] |
| 2.2-T7 | Recall check | synthetic bad set | run lexical only | >= 70 % flagged | [ ] |
| 2.2-T8 | Empty/odd host | none | `""`, `localhost`, `1.2.3.4` | no crash; IP flagged | [ ] |

**7. Verification:** [ ] T1-T8 [ ] numbers from T6/T7 recorded in `docs/eval-latest.md`.
**8. Completion:** offline lexical layer meets FPR/recall sub-targets.

**9. Git**
```bash
git status
git add .
git commit -m "feat(intel): lexical gibberish and brand-lookalike analysis"
git push origin main
```
**10. Rollback:** R2; the trained JSON is regenerated by the script.

---

## Milestone 2.3 - Safe redirect resolver (SSRF-guarded)

**1. Name:** Follow short links and redirects without endangering the server.
**Depends on:** 2.1.

**2. Objective:** Reveal the real destination behind `bit.ly`, `t.co`, `tinyurl`, `cutt.ly`, `wa.me` redirects and open redirectors, and detect dead links.

**3. Tasks**
- [ ] `app/intel/resolver.py` using `httpx` with: max 8 hops, per-request 4 s / total 10 s timeouts, response size cap (read at most 512 KB), `HEAD` first then `GET` fallback, manual redirect following.
- [ ] **SSRF guard:** before each hop resolve DNS and reject private/loopback/link-local/metadata IPs (`127.0.0.0/8`, `10/8`, `172.16/12`, `192.168/16`, `169.254.169.254`, `::1`, `fc00::/7`), reject non-http(s) schemes and unusual ports (allow 80/443/8080/8443), re-check on every redirect, pin the resolved IP for the connection (prevents DNS rebinding).
- [ ] Return: chain list, final URL, final status, `outcome` in {`OK`, `NXDOMAIN`, `NOT_FOUND`(404/410), `CONNECT_FAILED`, `TIMEOUT`, `BLOCKED_BY_GUARD`, `LOOP`, `TOO_MANY_HOPS`}.
- [ ] Known shortener list as a signal (`SHORTENED_URL`), and redirect-to-different-registrable-domain signal.
- [ ] Open-redirector awareness (`google.com/url?q=`, `facebook.com/l.php?u=`): follow and judge the final host.

**4. Files:** `app/intel/resolver.py`, `app/intel/netguard.py`, `tests/test_resolver.py`.

**5. Guidance:** This is the riskiest module for the server itself; keep it small and fully tested. No JavaScript is ever executed. User-Agent is a normal browser string (some phishing kits cloak against bots; note this limitation in docs).

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 2.3-T1 | Simple redirect | respx: a->b->c | resolve a | chain length 3, final c | [ ] |
| 2.3-T2 | SSRF loopback | none | resolve `http://127.0.0.1:8000/` | `BLOCKED_BY_GUARD`, no request sent | [ ] |
| 2.3-T3 | Metadata IP | none | `http://169.254.169.254/latest/meta-data` | blocked | [ ] |
| 2.3-T4 | Redirect to private IP | respx: public -> `http://10.0.0.5` | resolve | blocked at hop 2 | [ ] |
| 2.3-T5 | DNS rebinding | mock DNS returns public then private | resolve | pinned IP used or blocked | [ ] |
| 2.3-T6 | Dead link | respx 404 | resolve | `NOT_FOUND` | [ ] |
| 2.3-T7 | NXDOMAIN | mock DNS failure | resolve | `NXDOMAIN` | [ ] |
| 2.3-T8 | Loop | respx a->b->a | resolve | `LOOP` within 8 hops | [ ] |
| 2.3-T9 | Huge body | respx 50 MB stream | resolve | reads <= 512 KB, no memory spike | [ ] |
| 2.3-T10 | Live (mark live) | internet | resolve a real bit.ly | final URL returned | [ ] |

**7. Verification:** [ ] T1-T9 offline pass [ ] manual SSRF attempt from the running API fails [ ] T10 once.
**8. Completion:** resolver cannot reach internal addresses under any redirect path.

**9. Git**
```bash
git status
git add .
git commit -m "feat(intel): SSRF-guarded redirect resolver and dead-link detection"
git push origin main
```
**10. Rollback:** R2. If already deployed, disable via feature flag `ENABLE_NETWORK_INTEL=false` (add this flag here).

---

## Milestone 2.4 - Domain facts: DNS, RDAP age, TLS certificate

**1. Name:** Objective domain facts.
**Depends on:** 2.3.

**2. Objective:** Domain age and registrar, DNS sanity, certificate age/issuer — the strongest free indicators for new phishing domains.

**3. Tasks**
- [ ] `uv add dnspython`.
- [ ] `app/intel/domain_facts.py`: RDAP lookup via `https://rdap.org/domain/<d>` (follows IANA bootstrap), parse `registration`/`expiration`/`registrar`; fail soft (many ccTLDs omit data; `.in` supports RDAP).
- [ ] Signals: `DOMAIN_AGE_LT_30D`, `DOMAIN_AGE_LT_1Y`, `DOMAIN_AGE_GT_5Y` (positive), `PRIVACY_REDACTED` (neutral), `NO_MX/NO_A`.
- [ ] TLS: stdlib `ssl` handshake on 443 with 3 s timeout; certificate issuer, `notBefore` age, name match; signals `CERT_NEW_LT_14D`, `CERT_FREE_ISSUER` (neutral by itself), `CERT_MISMATCH`, `NO_TLS`.
- [ ] Cache results in memory (TTL 24 h) keyed by registrable domain.

**4. Files:** `app/intel/domain_facts.py`, `app/intel/cache.py`, `tests/test_domain_facts.py`.

**5. Guidance:** Free certificates (Let's Encrypt) are used by both attackers and legitimate sites, so they are never used alone. Missing RDAP data = `UNKNOWN`, never negative.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 2.4-T1 | Young domain | respx RDAP created 5 days ago | analyze | `DOMAIN_AGE_LT_30D` | [ ] |
| 2.4-T2 | Old domain | RDAP 2005 | analyze | positive age signal | [ ] |
| 2.4-T3 | RDAP unavailable | respx 500/timeout | analyze | status UNKNOWN, no exception | [ ] |
| 2.4-T4 | Cert mismatch | mocked ssl | analyze | `CERT_MISMATCH` | [ ] |
| 2.4-T5 | No HTTPS | connection refused 443 | analyze | `NO_TLS` | [ ] |
| 2.4-T6 | Cache | call twice | second call | no network (assert respx call count 1) | [ ] |
| 2.4-T7 | Live (mark live) | internet | `sbi.co.in`, `google.com` | ages > 5 y, valid cert | [ ] |

**7. Verification:** [ ] T1-T6 offline [ ] T7 once [ ] latency of the module with 4 concurrent lookups < 4 s.
**8. Completion:** domain facts returned as structured findings; failures never raise.

**9. Git**
```bash
git status
git add .
git commit -m "feat(intel): RDAP domain age, DNS and TLS certificate analysis"
git push origin main
```
**10. Rollback:** R2; remove `dnspython` via revert.

---

## Milestone 2.5 - Reputation providers (free tiers)

> **KEY GATE B:** before starting, stop and ask the user for the Safe Browsing and VirusTotal keys using `KEYS.md` (Gate B).

**1. Name:** Threat-intel lookups.
**Depends on:** 2.1 (2.4 for the cache module).

**2. Objective:** Ask the free security services whether a URL/domain is known-bad, with graceful degradation.

**3. Tasks**
- [ ] Provider interface `ReputationProvider.check(parsed_url) -> Finding`.
- [ ] **Google Safe Browsing v4 Lookup** (key from Google Cloud console, free for non-commercial use).
- [ ] **VirusTotal v3 URL report** (free: 4 requests/min, 500/day): only called when other signals are inconclusive or the domain is not on the trusted registry, to conserve quota; token-bucket rate limiter.
- [ ] **URLhaus** host/URL lookup (abuse.ch Auth-Key).
- [ ] **OpenPhish** community feed downloaded at startup and refreshed every 12 h into a local set (zero per-request cost).
- [ ] Optional **PhishTank** behind a flag (registration is often closed).
- [ ] Aggregate: `known_malicious` if any decisive hit; record which providers answered (feeds confidence in 3.3).
- [ ] Each provider: 3 s timeout, one retry, circuit breaker after 3 consecutive failures for 5 min.

**4. Files:** `app/intel/reputation/{base,safebrowsing,virustotal,urlhaus,openphish}.py`, `app/intel/ratelimit.py`, `tests/test_reputation.py`.

**5. Guidance:** Never call providers for trusted-registry domains except Safe Browsing (cheap) to save quota; log provider availability but never keys. Keep each provider's raw verdict string in the evidence trail so the report can say "Flagged by Google Safe Browsing: SOCIAL_ENGINEERING".

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 2.5-T1 | Safe Browsing hit | respx returns `matches` | check | `KNOWN_MALICIOUS` finding w/ threat type | [ ] |
| 2.5-T2 | Clean | respx `{}` | check | `CLEAN` finding | [ ] |
| 2.5-T3 | Key missing | provider unconfigured | run aggregate | provider skipped, others run, `coverage` reduced | [ ] |
| 2.5-T4 | VT rate limit 429 | respx 429 | check | no exception, `UNAVAILABLE`, bucket backs off | [ ] |
| 2.5-T5 | Circuit breaker | 3 failures | 4th call | not attempted for 5 min | [ ] |
| 2.5-T6 | OpenPhish feed | respx feed text | URL in feed | hit; URL not in feed -> clean | [ ] |
| 2.5-T7 | All providers down | all fail | aggregate | `UNAVAILABLE`, engine still returns | [ ] |
| 2.5-T8 | Quota guard | trusted domain | aggregate | VT not called | [ ] |
| 2.5-T9 | Live (mark live) | keys set | known OpenPhish URL from today's feed | flagged by >= 1 provider | [ ] |

**7. Verification:** [ ] T1-T8 offline [ ] T9 once [ ] no key appears in logs (`grep` log output).
**8. Completion:** any subset of providers can be missing without errors.

**9. Git**
```bash
git status
git add .
git commit -m "feat(intel): Safe Browsing, VirusTotal, URLhaus, OpenPhish reputation providers"
git push origin main
```
Not committed: `.env`, feed dumps.
**10. Rollback:** R2. If a key was committed by mistake: rotate first.

---

## Milestone 2.6 - Trust registry (safe-site knowledge, any category, India-weighted)

**1. Name:** Positive trust signals so real sites are never flagged.
**Depends on:** 2.2.

**2. Objective:** Genuine sites in **every** category (banks, UPI apps, government, e-commerce, travel, telecom, education, health, media, social, tech, jobs, delivery, crypto exchanges, utilities, news) are recognised as safe; scale comes from data, not hand-coded brand rules.

**3. Tasks**
- [ ] `scripts/build_trust_data.py`: download Tranco top 100k (at build time; git-ignored), keep registrable domains with rank; output `app/intel/data/tranco_100k.txt.gz`.
- [ ] Curated `app/intel/data/official_domains.json`: `{brand, category, domains[], aliases[], country}` seeded with 500+ entries: Indian banks (SBI, HDFC, ICICI, Axis, Kotak, PNB, BoB, Canara, Union, IDFC, Yes, IndusInd...), UPI/payments (Google Pay, PhonePe, Paytm, BHIM, Amazon Pay, CRED, MobiKwik, Razorpay...), government (`*.gov.in`, `*.nic.in`, IRCTC, UIDAI, Income Tax, EPFO, DigiLocker, UMANG, NPCI, RBI, Passport Seva), telecom (Jio, Airtel, Vi, BSNL), e-commerce (Amazon, Flipkart, Myntra, Meesho, Nykaa, Ajio, BigBasket, Swiggy, Zomato), travel (MakeMyTrip, Goibibo, IRCTC, Ixigo, airlines), media/music (Spotify, YouTube, JioSaavn, Hotstar, Netflix), social (WhatsApp, Instagram, Facebook, X, LinkedIn, Telegram), tech (Google, Microsoft, Apple), delivery (India Post, Delhivery, BlueDart, DTDC), jobs (Naukri, LinkedIn), health, education (`*.ac.in`, `*.edu.in`), crypto (WazirX, CoinDCX), news.
- [ ] Suffix rules: `*.gov.in`, `*.nic.in`, `*.ac.in`, `*.edu.in`, `*.res.in`, `*.mil.in`, `*.gov`, `*.edu` are trusted **only if the full registrable suffix matches** (blocks `gov-in-login.com`).
- [ ] Trust tiers: `OFFICIAL` (in registry, exact registrable domain match), `POPULAR` (Tranco rank <= 100k), `UNKNOWN`.
- [ ] **User-content platforms:** (`blogspot.com`, `github.io`, `sites.google.com`, `drive.google.com`, `forms.gle`, `docs.google.com/forms`, `notion.site`, `wixsite.com`, `weebly.com`, `web.app`, `pages.dev`, `vercel.app`, `herokuapp.com`, `s3.amazonaws.com`, `firebaseapp.com`, `bit.ly` etc.) are *not* trusted at path level: the platform is trusted but content on it must still be inspected (2.7) and capped at `SUSPICIOUS` unless it passes inspection.
- [ ] Stronger brand lookalike: a domain that looks like an OFFICIAL brand but is not in its `domains` is the top-weighted negative signal.
- [ ] Positive findings: `TRUSTED_OFFICIAL`, `TRUSTED_POPULAR`.

**4. Files:** `scripts/build_trust_data.py`, `app/intel/trust.py`, `app/intel/data/official_domains.json`, `tests/test_trust.py`.

**5. Guidance:** Tranco rank alone is a heuristic: popular domains can host user content (handled above) or be compromised (cannot be detected statically; mitigated by reputation feeds still being queried via Safe Browsing). The registry is extendable by anyone via a PR-sized JSON edit, which is how it "targets everything" over time.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 2.6-T1 | Real bank | registry | `https://www.onlinesbi.sbi/login` | `TRUSTED_OFFICIAL`, no keyword penalty | [ ] |
| 2.6-T2 | Gov suffix | none | `https://uidai.gov.in` | trusted | [ ] |
| 2.6-T3 | Fake gov | none | `gov-in-verify.com` | NOT trusted; lookalike flag | [ ] |
| 2.6-T4 | Popular non-registry | tranco | a rank-5000 site | `TRUSTED_POPULAR` | [ ] |
| 2.6-T5 | User-content host | none | `https://abc.blogspot.com/login` | platform known, path not trusted | [ ] |
| 2.6-T6 | Subdomain abuse | none | `sbi.co.in.evil.com` | NOT trusted (registrable domain is evil.com) | [ ] |
| 2.6-T7 | FPR | Phase 1 safe set | classify trust tier | >= 95 % of safe set is OFFICIAL/POPULAR | [ ] |
| 2.6-T8 | Registry validation | json | schema test | every entry has brand, category, domains | [ ] |

**7. Verification:** [ ] T1-T8 [ ] registry reviewed for typos by a teammate [ ] Tranco file builds in the Docker image (checked in 9.1).
**8. Completion:** real sites across categories resolve to trusted; lookalikes do not.

**9. Git**
```bash
git status
git add .
git commit -m "feat(intel): trust registry, Tranco popularity and user-content platform handling"
git push origin main
```
Not committed: the raw Tranco CSV (only the compact processed file if < 2 MB, else build at deploy).
**10. Rollback:** R2.

---

## Milestone 2.7 - Sandboxed page inspection

**1. Name:** Look at what the page actually is.
**Depends on:** 2.3, 2.6.

**2. Objective:** For non-trusted, reachable pages, fetch the HTML (no JavaScript execution) and look for credential harvesting and brand impersonation.

**3. Tasks**
- [ ] `uv add selectolax` (fast HTML parser; lighter than a headless browser, which would not fit Render free RAM).
- [ ] `app/intel/page.py`: reuse the resolver's guarded client; cap at 512 KB and `text/html` only.
- [ ] Extract: `<title>`, visible text snippet, forms with `type=password`/OTP/card/Aadhaar/PAN fields, form `action` host vs page host (cross-domain post), meta refresh and JS `location=` redirects, hidden iframes, brand names/logos alt text in the page vs the domain, "download APK" links, favicon hash vs known brands (optional).
- [ ] Signals: `LOGIN_FORM_ON_UNTRUSTED`, `FORM_POSTS_TO_OTHER_DOMAIN`, `BRAND_MISMATCH_PAGE` (page says "HDFC Bank" but domain isn't HDFC), `APK_DOWNLOAD`, `PAGE_EMPTY_OR_PARKED`, `PAGE_REACHABLE_NORMAL`.
- [ ] Optional: send title+text excerpt (not the whole page) to Gemini for a structured "is this a credential-harvesting page imitating X?" opinion; used as a *supporting* signal only.
- [ ] Skip entirely for `OFFICIAL`/`POPULAR` domains (cost and risk).

**4. Files:** `app/intel/page.py`, `tests/fixtures/pages/*.html`, `tests/test_page.py`.

**5. Guidance:** Cloaking (phishing kits that hide from servers) means "page looked fine" is weak positive evidence; it never alone yields `SAFE` for an untrusted domain with other bad signals. Document this limitation.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 2.7-T1 | Fake bank login | fixture HTML titled "HDFC NetBanking", password field, domain `x.top` | inspect | `LOGIN_FORM_ON_UNTRUSTED` + `BRAND_MISMATCH_PAGE` | [ ] |
| 2.7-T2 | Cross-domain form | form action to other host | inspect | `FORM_POSTS_TO_OTHER_DOMAIN` | [ ] |
| 2.7-T3 | Harmless blog | fixture blog | inspect | `PAGE_REACHABLE_NORMAL` | [ ] |
| 2.7-T4 | Non-HTML | respx returns PDF | inspect | skipped, no crash | [ ] |
| 2.7-T5 | Malformed HTML | broken markup | inspect | no exception | [ ] |
| 2.7-T6 | Trusted skip | `sbi.co.in` | inspect | not fetched | [ ] |
| 2.7-T7 | Script injection | page with `<script>` | inspect | script never executed (parser only) | [ ] |
| 2.7-T8 | Timeout | slow server | inspect | `TIMEOUT` finding in 10 s max | [ ] |

**7. Verification:** [ ] T1-T8 [ ] run against 5 current phishing URLs from the feed in an isolated way (never open them in a browser).
**8. Completion:** page-level evidence available without code execution.

**9. Git**
```bash
git status
git add .
git commit -m "feat(intel): sandboxed HTML inspection for credential-harvesting detection"
git push origin main
```
**10. Rollback:** R2; set `ENABLE_PAGE_INSPECTION=false` if already deployed.

---

## Phase 2 Completion Checkpoint
| Item | Record |
|---|---|
| Completed milestones | 2.1-2.7 |
| Tests passed | all `2.x-T*`, full regression |
| Known issues | cloaked phishing pages; RDAP gaps for some ccTLDs; provider quotas |
| Git hash | (fill) |
| Overall verification | `evaluate.py` URL-only: record detection + FPR; expected clearly above baseline even before Phase 3 scoring |
| Go/No-Go | Go if URL FPR <= 5 % and recall >= 80 % (final gate is Phase 3.4) |

```bash
git tag -a phase-2-done -m "Phase 2 complete" && git push origin main phase-2-done
```
