"""
Formal e-mail benchmark (rules only; no AI calls).

Genuine institutional e-mails must NEVER be flagged; formal phishing e-mails must be.
Includes the two real e-mails that exposed false alarms (NSE balance mail, ICICI GST invoice).

    uv run python scripts/eval_emails.py [--net]
"""

import sys
from pathlib import Path

from app.engine.analysis import Case, investigate_sync

BASE = Path(__file__).resolve().parents[2] / "data" / "benchmark" / "emails"


def load():
    items = []
    for block in (BASE / "corpus.txt").read_text(encoding="utf-8").split("### ")[1:]:
        head, _, body = block.partition("\n")
        label, name = [x.strip() for x in head.split("|")]
        items.append((label, name, body.strip()))
    for f in sorted(BASE.glob("*.txt")):
        if f.name != "corpus.txt":
            items.append(("genuine", f.stem, f.read_text(encoding="utf-8")))
    return items


def main():
    net = "--net" in sys.argv
    bad_genuine, bad_scam = [], []
    items = load()
    for label, name, text in items:
        r = investigate_sync(Case(text, network=net)).result
        flagged = r["verdict"] in {"SUSPICIOUS", "DANGEROUS"}
        if label == "genuine" and (flagged or r["risk_score"] > 10):
            bad_genuine.append((name, r["verdict"], r["risk_score"]))
        if label == "scam" and not flagged:
            bad_scam.append((name, r["verdict"], r["risk_score"]))
    g = sum(1 for l, _, _ in items if l == "genuine")
    s = len(items) - g
    print(f"emails: {g} genuine, {s} scam (network={'on' if net else 'off'})")
    print(f"genuine flagged or scored above 10: {len(bad_genuine)}/{g}  {bad_genuine}")
    print(f"scams missed: {len(bad_scam)}/{s}  {bad_scam}")
    sys.exit(1 if bad_genuine or bad_scam else 0)


if __name__ == "__main__":
    main()
