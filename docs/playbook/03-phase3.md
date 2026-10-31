# Phase 3 - Scoring, Verdict & Confidence Engine

Branch: work directly on `main` (push after every verified milestone).

---

## Milestone 3.1 - Signal model v2 (positive and negative evidence)

**1. Name:** Unified Finding/Signal model.
**Depends on:** Phase 2.

**2. Objective:** Every piece of evidence from Phase 2 and the message analyser becomes a typed signal with polarity, weight, source, target and a human sentence.

**3. Tasks**
- [ ] Extend `app/graph/signals.py`: `Signal(id, polarity: risk|trust|neutral, weight, strength: weak|moderate|strong|decisive, target, source, explanation)`.
- [ ] Weight table in one file `app/engine/weights.py`: decisive risk (feed hit, official-brand lookalike, credential form on untrusted domain) vs. trust (OFFICIAL domain, clean across providers, old domain).
- [ ] Per-target aggregation: signals grouped per URL, message-level signals grouped separately.
- [ ] Deduplicate by `(id, target)` (keeps current dedupe behaviour, tested for regression).
- [ ] Adapter so existing nodes keep working during migration.

**4. Files:** `app/graph/signals.py`, `app/engine/weights.py`, `app/graph/state.py`, `tests/test_signals.py`.

**5. Guidance:** Weights are data, versioned (`WEIGHTS_VERSION`) and returned in the API so a report can be reproduced. 3.4 tunes them; do not hand-tune here.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 3.1-T1 | Dedupe | two identical signals | aggregate | one counted | [ ] |
| 3.1-T2 | Polarity | trust + risk signal | aggregate per target | both retained, net computed later | [ ] |
| 3.1-T3 | Unknown id | signal id not in table | construct | raises clear error | [ ] |
| 3.1-T4 | Regression | old URL_* signals | adapter | same ids map to new ones | [ ] |
| 3.1-T5 | Serialisation | any signal | `model_dump_json` | round-trips | [ ] |

**7. Verification:** [ ] T1-T5 [ ] Phase 0-2 suites still green.
**8. Completion:** one signal vocabulary used everywhere.

**9. Git**
```bash
git status
git add .
git commit -m "feat(engine): signal model v2 with polarity, strength and versioned weights"
git push origin main
```
**10. Rollback:** R2.

---

## Milestone 3.2 - Verdict decision logic

**1. Name:** Rule-based verdict with explicit overrides.
**Depends on:** 3.1.

**2. Objective:** Implement the sponsor's logic exactly: obviously fake -> DANGEROUS, genuine -> SAFE, non-existent but legitimate-looking -> COULD_NOT_VERIFY.

**3. Tasks**
- [ ] `app/engine/verdict.py` evaluated **in this order** per URL:
  1. Decisive bad: feed hit (Safe Browsing/URLhaus/OpenPhish/VT >= 3 engines) -> `DANGEROUS`.
  2. Lexically fake (gibberish, official-brand lookalike, homograph, raw IP, credential form on untrusted) -> `DANGEROUS` **even if the domain does not resolve**.
  3. Unreachable (`NXDOMAIN`, 404/410, connect failure) and domain looks legitimate -> `COULD_NOT_VERIFY` (message says "link is dead or does not exist").
  4. `OFFICIAL` trust, no risk signals -> `SAFE`.
  5. `POPULAR` or older-domain + clean reputation + normal page, no risk signals -> `SAFE`.
  6. Some moderate risk signals -> `SUSPICIOUS`.
  7. Nothing decisive either way (new unknown domain, clean feeds, normal page) -> `SUSPICIOUS` (low) rather than SAFE; sponsor wants unknown junk flagged.
- [ ] Message-level verdict = worst URL verdict, combined with message signals (OTP request, urgency). Dead link inside a scam-pattern message: message `DANGEROUS`/`SUSPICIOUS`, URL status shown as unreachable.
- [ ] A user-content platform URL never exceeds `SUSPICIOUS` unless inspection passes.
- [ ] Output `verdict`, `risk_score` (0-100 monotonic with verdict band: SAFE 0-19, SUSPICIOUS 20-59, DANGEROUS 60-100, COULD_NOT_VERIFY null), `risk_level` derived for UI compatibility, and `decision_path` (list of rule ids that fired) for explainability.

**4. Files:** `app/engine/verdict.py`, `app/graph/nodes/risk_assessment.py`, `tests/test_verdict.py`.

**5. Guidance:** The order of rules is the product behaviour; keep it a small readable table, not nested ifs. `decision_path` makes every verdict auditable in the sponsor demo.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 3.2-T1 | Gibberish, NXDOMAIN | signals: gibberish + NXDOMAIN | verdict | DANGEROUS | [ ] |
| 3.2-T2 | Legit-looking, NXDOMAIN | clean lexical + NXDOMAIN | verdict | COULD_NOT_VERIFY | [ ] |
| 3.2-T3 | Real bank | OFFICIAL + login form on official domain | verdict | SAFE | [ ] |
| 3.2-T4 | Feed hit on popular domain | POPULAR + Safe Browsing hit | verdict | DANGEROUS (feed overrides trust) | [ ] |
| 3.2-T5 | Dead link in scam text | message urgency + OTP + 404 link | verdict | message DANGEROUS/SUSPICIOUS, URL unreachable noted | [ ] |
| 3.2-T6 | Blogspot phishing | user-content + login form | verdict | not SAFE | [ ] |
| 3.2-T7 | No evidence | empty | verdict | SAFE only if no URLs/no message risk; otherwise COULD_NOT_VERIFY | [ ] |
| 3.2-T8 | Score/verdict agreement | random fuzz of 1000 signal sets | assert band matches verdict | always | [ ] |

**7. Verification:** [ ] T1-T8 [ ] `decision_path` present on every response.
**8. Completion:** verdict never contradicts score; sponsor rules encoded as tests.

**9. Git**
```bash
git status
git add .
git commit -m "feat(engine): deterministic verdict rules incl. dead-link and gibberish handling"
git push origin main
```
**10. Rollback:** R2.

---

## Milestone 3.3 - Evidence-based confidence

**1. Name:** Confidence that means something.
**Depends on:** 3.2.

**2. Objective:** Confidence is computed from coverage and agreement, not invented by the LLM.

**3. Tasks**
- [ ] Define `coverage` = weighted fraction of applicable checks that completed (lexical, resolver, domain facts, trust, each reputation provider, page inspection, message analysis).
- [ ] Define `agreement` = share of decisive/strong signals that point to the final verdict.
- [ ] `confidence = clamp(0.25 + 0.4*coverage + 0.35*agreement, 0.05, 0.99)`; overrides: decisive feed hit or OFFICIAL domain with all checks clean -> >= 0.95; COULD_NOT_VERIFY -> <= 0.5; all providers unavailable -> cap 0.6.
- [ ] Expose `confidence_factors` (coverage %, agreement %, missing checks) in the API.
- [ ] Remove `confidence` from the Gemini schema (Gemini no longer outputs it).

**4. Files:** `app/engine/confidence.py`, `app/services/gemini_schema.py`, `tests/test_confidence.py`.

**5. Guidance:** The formula is intentionally simple and documented so it can be defended in the viva; calibration in 3.4 checks that confidence correlates with correctness (reliability table).

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 3.3-T1 | Full coverage + agree | all checks done | compute | >= 0.9 | [ ] |
| 3.3-T2 | Providers down | reputation unavailable | compute | lower than T1, factors list missing providers | [ ] |
| 3.3-T3 | Feed hit | decisive signal | compute | >= 0.95 | [ ] |
| 3.3-T4 | Conflicting evidence | trust + risk signals | compute | <= 0.7 | [ ] |
| 3.3-T5 | Bounds | fuzz | all outputs | within [0.05, 0.99] | [ ] |
| 3.3-T6 | Determinism | same input twice | compute | identical | [ ] |

**7. Verification:** [ ] T1-T6 [ ] no `confidence` produced by Gemini anywhere (`grep`).
**8. Completion:** confidence reproducible and explainable.

**9. Git**
```bash
git status
git add .
git commit -m "feat(engine): evidence-based confidence from coverage and agreement"
git push origin main
```
**10. Rollback:** R2.

---

## Milestone 3.4 - Calibration against the benchmark (quality gate)

**1. Name:** Tune weights to hit the accuracy targets.
**Depends on:** 3.3, Phase 1.

**2. Objective:** Reach detection >= 90 %, FPR <= 3 %, overall >= 90 % (hard floor 85 %) on URL + message benchmarks.

**3. Tasks**
- [ ] Run `evaluate.py --offline` (recorded provider fixtures) then `--live` for the URL corpus.
- [ ] Review every misclassification; fix by adding a signal or rule, **not** by memorising the sample.
- [ ] Hold out 20 % of benchmark rows as a test split that you never tune on (`split` column); report both.
- [ ] Reliability table: bucket confidence 0.5-0.6 ... 0.9-1.0 and show actual accuracy per bucket.
- [ ] Freeze `WEIGHTS_VERSION`; commit `docs/eval-latest.md`.

**4. Files:** `app/engine/weights.py`, `data/benchmark/*`, `docs/eval-latest.md`.

**5. Guidance:** Over-fitting to your own benchmark is the main risk; the held-out split and a fresh batch of live feed URLs fetched on demo day are the honest check.

**6. Tests**

| ID | Scenario | Preconditions | Steps | Expected | Status |
|---|---|---|---|---|---|
| 3.4-T1 | Detection gate | URL set | evaluate | >= 90 % | [ ] |
| 3.4-T2 | FPR gate | safe set | evaluate | <= 3 % | [ ] |
| 3.4-T3 | Hold-out | split=test | evaluate | within 3 points of train | [ ] |
| 3.4-T4 | Message set | messages.csv | evaluate | >= 90 % overall | [ ] |
| 3.4-T5 | Fresh feed batch | live | today's 50 new phish URLs | >= 85 % | [ ] |
| 3.4-T6 | Calibration | table | high-confidence bucket | accuracy >= 95 % | [ ] |
| 3.4-T7 | Regression | all earlier suites | pytest | green | [ ] |

**7. Verification:** [ ] gates pass or documented gap with plan [ ] numbers copied to the sponsor report.
**8. Completion:** accuracy gates met on benchmark.

**9. Git**
```bash
git status
git add .
git commit -m "tune(engine): calibrate weights; URL/message benchmark gates met"
git push origin main
```
**10. Rollback:** R2; weights are one file, so reverting restores earlier behaviour.

---

## Phase 3 Completion Checkpoint
| Item | Record |
|---|---|
| Completed milestones | 3.1-3.4 |
| Tests passed | all `3.x-T*` |
| Known issues | list misclassified categories |
| Git hash | (fill) |
| Overall verification | `evaluate.py` gates green |
| Go/No-Go | Go only if gates (or the agreed floor) pass |

```bash
git tag -a phase-3-done -m "Phase 3 complete" && git push origin main phase-3-done
```
