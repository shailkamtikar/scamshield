# ScamShield Production Playbook — Index, Conventions, Open Questions

Goal: take ScamShield from the current prototype to a deployed (Vercel + Render, free tiers only) scam/phishing detector for the sponsor, with measured accuracy (>= 85-90 %) and a polished dark UI.

## Files

| File | Phases |
|---|---|
| `00-README.md` | This file: conventions, dependency map, confirmed decisions |
| `KEYS.md` | Step-by-step guide to obtain every API key / account (key gates) |
| `01-phase0-1.md` | Phase 0 Setup & Baseline, Phase 1 Benchmark & Evaluation |
| `02-phase2.md` | Phase 2 URL Intelligence Core |
| `03-phase3.md` | Phase 3 Scoring, Verdict & Confidence Engine |
| `04-phase4-5.md` | Phase 4 Text/SMS pipeline, Phase 5 Image pipeline |
| `05-phase6.md` | Phase 6 QR pipeline |
| `06-phase7.md` | Phase 7 API hardening & streaming |
| `07-phase8.md` | Phase 8 Frontend redesign |
| `08-phase9-release.md` | Phase 9 Deployment & docs, Final Release Checklist |

## Decisions confirmed by the team

1. **API keys: none in hand yet.** Work stops at defined **KEY GATES** and asks for the key with step-by-step instructions from `KEYS.md` (Gate A before 1.1 for abuse.ch, Gate B before 2.5 for Safe Browsing + VirusTotal, Gate C before 9.1 for Render/Vercel/UptimeRobot accounts). Gemini is the only key assumed to exist already (verified in 0.3).
2. **Python tooling:** `uv` is kept (lockfile exists, fast, works in Docker). It is an implementation detail and can be swapped without affecting the plan.
3. **Branching:** everything is committed and pushed straight to `main` after each verified milestone (repo layout: `backend/`, `frontend/`, `docs/`, `data/`). Because `main` is the only branch, CI must be green *before* each push (run the suite locally first) and, once Phase 9 connects Render/Vercel, every push to `main` auto-deploys.
4. **Render:** free web service (512 MB RAM, ephemeral disk, spin-down mitigated by an uptime robot).
5. **Acceptance numbers (confirmed):** detection >= 90 %, false positives on safe links <= 3 %, overall >= 90 % (hard floor 85 %).
6. **Design bar:** looks like a 10k-budget agency site, not template/AI-generic output. See `07-phase8.md` art direction.
7. **Live camera QR scanning** inside the web app is in scope (Milestone 8.3A): the phone decodes the QR in the browser and only the decoded text goes to the backend, so the QR destination is never opened by the user.

## Global rules

### Git identity and "no co-contributor" rule
- Every commit must be authored only by you. **Never** add `Co-Authored-By:` trailers, never add collaborators on GitHub, never pass `--trailer`.
- Before the first commit: `git config user.name` and `git config user.email` must be yours.
- Audit any time (must print only your name and no trailer lines):
```bash
git log --format='%h %an <%ae>%n%b' | grep -iE "co-authored|claude|anthropic" || echo "clean: no co-authors"
git shortlog -sne --all
```
- GitHub contributors graph: Settings -> Collaborators must list only you / your team.

### Never commit
`.env`, `.env.*` (except `.env.example`), any API key, `backend/.venv`, `__pycache__`, `node_modules`, `frontend/dist`, `data/raw/` (downloaded feeds), `data/cache/`, `*.log`, coverage output, `midsem/`, personal screenshots. Before every commit: `git status` then `git diff --cached --stat`; if anything above appears, `git restore --staged <path>`.

### Secrets leak check (run before every push)
```bash
git diff --cached | grep -iE "AIza|api[_-]?key|secret|token|Auth-Key" && echo "STOP: possible secret" || echo "ok"
```
If a secret was ever pushed: revoke/rotate the key first, then clean history. Deleting the file in a new commit is not enough.

### Milestone / test conventions
- Test status column: `[ ]` pending, `[P]` pass, `[F]` fail. A milestone is DONE only when all rows are `[P]`.
- Test IDs: `<milestone>-T<n>` (e.g. `2.3-T4`).
- Backend commands run from `backend/`: `uv run pytest -q`; frontend from `frontend/`: `npm run lint`, `npm run build`, `npm test`.
- Network-dependent tests are marked `@pytest.mark.live` and excluded from normal runs (`uv run pytest -m "not live"`); the default suite must pass offline using mocks.

### Standard Git checkpoint (used in every milestone)
```bash
git status
git add .          # only after confirming nothing from "Never commit" is staged
git commit -m "<message given in milestone>"
git push origin <branch-name>
```
Push only when the milestone's Verification Checklist is fully green.

### Standard rollback / recovery (referenced as "R1/R2/R3")
- **R1 - not pushed yet:** `git stash` (keep work) or `git reset --hard <last-checkpoint-hash>` (discard). Find the hash with `git log --oneline -5`.
- **R2 - pushed to a phase branch:** `git revert <bad-commit-hash>` then `git push origin <branch-name>`. For several commits: `git revert --no-commit <good-hash>..HEAD && git commit -m "revert: <milestone>"`.
- **R3 - merged into `main`:** same `git revert` on `main`; or recover from a phase tag: `git switch -c recover/<phase> phase-N-done`.
- Never `git push --force` on `main`. Every phase ends with an annotated tag: `git tag -a phase-N-done -m "Phase N complete" && git push origin main`.
- Each milestone below states anything extra to undo (dependencies, data files, deployed env vars).

## Dependency map

```
0.1 -> 0.2 -> 0.3 -> 0.4 -> 1.1, 1.2, 1.3 -> 1.4
1.4 -> 2.1 -> 2.2 -> 2.3 -> 2.4 -> 2.5 -> 2.6 -> 2.7
2.x -> 3.1 -> 3.2 -> 3.3 -> 3.4
3.4 -> 4.1 -> 4.2 -> 4.3
4.3 -> 5.1 -> 5.2 -> 5.3
4.3 -> 6.1 -> 6.2 -> 6.3 -> 6.4 -> 6.5
5.3 + 6.5 -> 7.1 -> 7.2 -> 7.3
7.1 -> 8.1 -> 8.2 -> 8.3 -> 8.3A -> 8.4 -> 8.5 -> 8.6 -> 8.7
7.3 + 8.7 -> 9.1 -> 9.2 -> 9.3 -> 9.4 -> Final Release Checklist
```
Phases 5 and 6 are independent of each other and can be done in either order after 4.3. Frontend 8.1-8.3 can start after 7.1 locks the API contract, but 8.4 requires streaming (7.1).

## Target verdicts (used everywhere)

| Verdict | Meaning |
|---|---|
| `SAFE` | Reachable, trusted or clean on all available checks, no deception signals. |
| `SUSPICIOUS` | Some deception signals but not conclusive. |
| `DANGEROUS` | Strong evidence: feed hit, lookalike/gibberish domain, credential-harvesting page, etc. A gibberish or obviously fake domain is DANGEROUS even if no feed has seen it. |
| `COULD_NOT_VERIFY` | Only when the destination does not exist or is unreachable (NXDOMAIN, 404/410, connection failure) **and** the domain itself looks legitimate. |

The old `risk_level` field (LOW/MEDIUM/HIGH/CRITICAL) is kept for UI compatibility and derived from the score.
