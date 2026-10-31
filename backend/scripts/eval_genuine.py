"""
Genuine-message benchmark (rules only; no AI calls).

Real-looking notices from many sectors (banks, KYC, telecom, utilities, transport, e-commerce, government,
brokers, insurance, health, schools) plus ordinary promotions. None of it was used to tune the rules.
A genuine message that is flagged, or scores above zero, is a bug; promotions must never be SUSPICIOUS or worse
unless their link is bad.

    uv run python scripts/eval_genuine.py [--show]
"""

import csv
import sys
from collections import defaultdict
from pathlib import Path

from app.engine.analysis import Case, investigate_sync

FILE = Path(__file__).resolve().parents[2] / "data" / "benchmark" / "messages_genuine.csv"


def main():
    show = "--show" in sys.argv
    rows = list(csv.DictReader(open(FILE, encoding="utf-8")))
    per = defaultdict(lambda: [0, 0])
    flagged, nonzero, wrong_promo = [], [], []
    n = {"genuine": 0, "promo": 0}
    for r in rows:
        res = investigate_sync(Case(r["text"], network=False)).result
        n[r["label"]] += 1
        per[r["category"]][1] += 1
        bad = res["verdict"] in {"SUSPICIOUS", "DANGEROUS"}
        if bad:
            flagged.append((res["verdict"], res["risk_score"], r["text"][:100]))
        elif res["risk_score"] > 0:
            nonzero.append((res["risk_score"], r["text"][:100]))
        else:
            per[r["category"]][0] += 1
        if r["label"] == "promo" and res.get("assurance") not in {"promotion", "promotion_unverified"}:
            wrong_promo.append((res["verdict"], res.get("assurance"), res.get("message_type"), r["text"][:90]))
    print(f"genuine messages {n['genuine']}, promotions {n['promo']}")
    print(f"flagged as SUSPICIOUS/DANGEROUS: {len(flagged)}/{len(rows)}")
    print(f"safe but scored above 0: {len(nonzero)}/{len(rows)}")
    print(f"promotions not recognised as promotions: {len(wrong_promo)}/{n['promo']}")
    if show:
        for x in flagged: print("  FLAGGED", x)
        for x in nonzero: print("  NONZERO", x)
        for x in wrong_promo: print("  PROMO?", x)
    sys.exit(1 if flagged else 0)


if __name__ == "__main__":
    main()
