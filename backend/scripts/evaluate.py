"""
Accuracy report for the URL benchmark.

    uv run python scripts/evaluate.py [--live] [--split test|train|all] [--show-errors N]

Default is STATIC mode: no network calls at all (lexical + trust checks only).
That measures how well the engine recognises NEW bad links nobody has listed
yet. --live also queries the real threat feeds for each link but never loads
the pages (page inspection is skipped), so no malicious page is ever opened.

Exit code is 1 if the quality gates fail.
"""

import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path

from app.config import settings
from app.engine.url_analysis import analyze_url
from app.intel.urls import parse_url

ROOT = Path(__file__).resolve().parents[2]
GATES = {"detection": 0.90, "false_positive": 0.03, "accuracy": 0.90}
FLAGGED = {"SUSPICIOUS", "DANGEROUS"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--split", default="all")
    ap.add_argument("--show-errors", type=int, default=0)
    ap.add_argument("--no-gate", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--include-malware", action="store_true", help="count malware-download links (not phishing) in the gate")
    args = ap.parse_args()

    if args.live:
        settings.enable_page_inspection = False  # never download suspicious pages
        settings.enable_fetch = False  # never even connect to suspicious sites

    rows = list(csv.DictReader(open(ROOT / "data" / "benchmark" / "urls.csv", encoding="utf-8")))
    if not args.include_malware:
        # malware-download links (often on github.com etc.) are a different problem from phishing
        rows = [r for r in rows if r["category"] != "malware_feed"]
    if args.split != "all":
        rows = [r for r in rows if r["split"] == args.split]

    if args.limit:
        import random
        random.Random(1).shuffle(rows)
        rows = rows[: args.limit]
    tp = fn = fp = tn = 0
    per_cat = defaultdict(lambda: Counter())
    errors = []
    for r in rows:
        parsed = parse_url(r["url"])
        if parsed is None:
            verdict = "UNPARSEABLE"
        else:
            verdict = analyze_url(parsed, network=args.live, inspect_page=False).verdict
        bad = r["label"] == "phish"
        flagged = verdict in FLAGGED or verdict == "UNPARSEABLE" and bad
        per_cat[r["category"]]["n"] += 1
        if bad and flagged:
            tp += 1
            per_cat[r["category"]]["ok"] += 1
        elif bad:
            fn += 1
            errors.append(("MISSED", r["category"], r["url"], verdict))
        elif flagged:
            fp += 1
            errors.append(("FALSE ALARM", r["category"], r["url"], verdict))
        else:
            tn += 1
            per_cat[r["category"]]["ok"] += 1

    detection = tp / max(tp + fn, 1)
    fpr = fp / max(fp + tn, 1)
    accuracy = (tp + tn) / max(len(rows), 1)
    precision = tp / max(tp + fp, 1)

    print(f"mode={'LIVE feeds' if args.live else 'STATIC (no network)'} split={args.split} n={len(rows)}")
    print(f"detection rate : {detection:.1%}  ({tp}/{tp + fn})")
    print(f"false positives: {fpr:.1%}  ({fp}/{fp + tn})")
    print(f"accuracy       : {accuracy:.1%}")
    print(f"precision      : {precision:.1%}")
    print("\nper category (correct/total):")
    for cat, c in sorted(per_cat.items()):
        print(f"  {cat:26} {c['ok']:4}/{c['n']:<4} {c['ok'] / c['n']:.0%}")
    if args.show_errors:
        print("\nerrors:")
        for kind, cat, url, verdict in errors[: args.show_errors]:
            print(f"  [{kind}] {cat}: {url[:100]} -> {verdict}")

    ok = detection >= GATES["detection"] and fpr <= GATES["false_positive"] and accuracy >= GATES["accuracy"]
    print("\nGATES:", "PASS" if ok else "FAIL", GATES)
    if not ok and not args.no_gate:
        sys.exit(1)


if __name__ == "__main__":
    main()
