"""
Accuracy report for the SMS benchmark (static: no network, no Gemini).

    uv run python scripts/eval_messages.py [--show-errors N]
"""

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path

from app.engine.analysis import Case, investigate_sync

ROOT = Path(__file__).resolve().parents[2]
FLAGGED = {"SUSPICIOUS", "DANGEROUS"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show-errors", type=int, default=0)
    ap.add_argument("--live", action="store_true")
    args = ap.parse_args()
    rows = list(csv.DictReader(open(ROOT / "data" / "benchmark" / "messages.csv", encoding="utf-8")))
    tp = fn = fp = tn = 0
    cat = defaultdict(lambda: [0, 0])
    errs = []
    for r in rows:
        res = investigate_sync(Case(r["text"], network=args.live)).result
        flagged = res["verdict"] in FLAGGED
        scam = r["label"] == "scam"
        ok = flagged == scam
        cat[r["category"]][0] += ok
        cat[r["category"]][1] += 1
        if scam and flagged: tp += 1
        elif scam: fn += 1; errs.append(("MISSED", r["text"], res["verdict"], res["risk_score"]))
        elif flagged: fp += 1; errs.append(("FALSE ALARM", r["text"], res["verdict"], res["risk_score"]))
        else: tn += 1
    det, fpr, acc = tp / max(tp + fn, 1), fp / max(fp + tn, 1), (tp + tn) / len(rows)
    print(f"messages n={len(rows)} mode={'live' if args.live else 'static'}")
    print(f"detection {det:.1%} ({tp}/{tp+fn})  false positives {fpr:.1%} ({fp}/{fp+tn})  accuracy {acc:.1%}")
    for k, (a, b) in sorted(cat.items()):
        print(f"  {k:14} {a}/{b} {a/b:.0%}")
    for kind, text, v, s in errs[: args.show_errors]:
        print(f"  [{kind}] {v}/{s}: {text[:130]}")
    if not (det >= 0.9 and fpr <= 0.03 and acc >= 0.9):
        print("GATES: FAIL"); sys.exit(1)
    print("GATES: PASS")


if __name__ == "__main__":
    main()
