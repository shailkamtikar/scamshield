"""
Red-team report: 75 hand-labelled scenarios across the categories (rules only, offline, no AI calls).

Expected categories were written by a person BEFORE running the engine and are never generated from its output.
Where the honest answer depends on evidence the text cannot carry (e.g. a brand-new domain) two categories are accepted,
written as A|B.

    uv run python scripts/eval_redteam.py [--show] [--llm]
"""

import csv
import sys
import time
import tracemalloc
from collections import Counter, defaultdict
from pathlib import Path

from app.engine.analysis import Case, investigate_sync

FILE = Path(__file__).resolve().parents[2] / "data" / "benchmark" / (sys.argv[sys.argv.index("--file") + 1] if "--file" in sys.argv else "redteam.csv")
BAD = {"PHISHING", "FRAUD_SCAM", "MALICIOUS_CONTENT"}
NOT_MALICIOUS = {"SAFE_TRANSACTIONAL", "SAFE_PROMOTIONAL", "SAFE_OTHER", "SPAM"}


def side(cat: str) -> str:
    return "malicious" if cat in BAD else "benign" if cat in NOT_MALICIOUS else "unsure"


def main():
    show = "--show" in sys.argv
    rows = list(csv.DictReader(open(FILE, encoding="utf-8")))
    tracemalloc.start()
    exact = 0
    fp, fn, n_benign, n_mal = [], [], 0, 0
    confusion = Counter()
    per_group = defaultdict(lambda: [0, 0])
    times = []
    for r in rows:
        expected = set(r["expected"].split("|"))
        t0 = time.perf_counter()
        res = investigate_sync(Case(r["text"], network=False)).result
        times.append(time.perf_counter() - t0)
        got = res["category"]
        ok = got in expected
        exact += ok
        per_group[r["group"]][0] += ok
        per_group[r["group"]][1] += 1
        confusion[(sorted(expected)[0], got)] += 1
        exp_sides = {side(e) for e in expected}
        if exp_sides == {"benign"}:
            n_benign += 1
            if side(got) == "malicious" or res["verdict"] in {"SUSPICIOUS", "DANGEROUS"}:
                fp.append((r["id"], got, res["verdict"], res["risk_score"], r["text"][:80]))
        if exp_sides == {"malicious"} or exp_sides == {"malicious", "unsure"}:
            n_mal += 1
            if side(got) == "benign":
                fn.append((r["id"], got, res["verdict"], res["risk_score"], r["text"][:80]))
        if show and not ok:
            print(f"  MISS #{r['id']:>2} expected {r['expected']:30} got {got:22} {res['verdict']}/{res['risk_score']} {r['text'][:70]}")
    peak = tracemalloc.get_traced_memory()[1] / 1e6
    print(f"scenarios: {len(rows)}   category exactly right: {exact}/{len(rows)} = {exact / len(rows):.1%}")
    print(f"false positives (benign flagged SUSPICIOUS/DANGEROUS or called malicious): {len(fp)}/{n_benign} = {len(fp) / max(n_benign, 1):.1%}")
    for x in fp: print("   FP", x)
    print(f"false negatives (malicious called benign): {len(fn)}/{n_mal} = {len(fn) / max(n_mal, 1):.1%}")
    for x in fn: print("   FN", x)
    print("per group:", {k: f"{a}/{b}" for k, (a, b) in sorted(per_group.items())})
    cats = sorted({c for c, _ in confusion} | {c for _, c in confusion})
    print("confusion (rows expected, columns got):")
    print("  " + " " * 22 + " ".join(c[:9].ljust(9) for c in cats))
    for e in cats:
        print("  " + e.ljust(22) + " ".join(str(confusion.get((e, c), 0)).ljust(9) for c in cats))
    print("per category (a prediction counts as right if it is any accepted label):")
    for cat in cats:
        tp_c = sum(v for (e, g), v in confusion.items() if g == cat and e == cat)
        pred = sum(v for (e, g), v in confusion.items() if g == cat)
        true = sum(v for (e, g), v in confusion.items() if e == cat)
        if not true and not pred:
            continue
        p_ = tp_c / pred if pred else 0.0
        r_ = tp_c / true if true else 0.0
        print(f"  {cat:24} n={true:<3} precision {p_:.0%}  recall {r_:.0%}  F1 {(2 * p_ * r_ / (p_ + r_)) if p_ + r_ else 0:.0%}")
    print(f"latency per message: median {sorted(times)[len(times) // 2] * 1000:.1f} ms, max {max(times) * 1000:.1f} ms; peak python memory {peak:.0f} MB")


if __name__ == "__main__":
    main()
