"""
Build the offline data files the intel layer needs from the Tranco list.

    uv run python scripts/build_trust_data.py [path/to/top-1m.csv]

Outputs (committed, small):
  app/intel/data/tranco_top.txt.gz   top-N registrable domains, one per line
  app/intel/data/lexical_model.json  character-trigram model + calibrated threshold
"""

import csv
import gzip
import json
import math
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import tldextract

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parents[1] / "app" / "intel" / "data"
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "raw" / "top-1m.csv"

TRUST_N = 50_000
TRAIN_N = 50_000
CALIBRATE_FROM, CALIBRATE_TO = 50_000, 250_000

extract = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)
ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789"


def words_of(label: str) -> list[str]:
    return [w for w in re.split(r"[^a-z0-9]+", label.lower()) if w]


def trigrams(word: str):
    padded = "^^" + word + "$"
    for i in range(2, len(padded)):
        yield padded[i - 2 : i], padded[i]


def main():
    domains: list[tuple[int, str, str]] = []
    with open(SRC, newline="", encoding="utf-8") as fh:
        for rank, domain in csv.reader(fh):
            ext = extract(domain)
            if ext.suffix and ext.domain:
                domains.append((int(rank), domain.lower(), ext.domain.lower()))
            if len(domains) >= CALIBRATE_TO:
                break

    OUT.mkdir(parents=True, exist_ok=True)

    with gzip.open(OUT / "tranco_top.txt.gz", "wt", encoding="utf-8") as fh:
        for _, domain, _ in domains[:TRUST_N]:
            fh.write(domain + "\n")

    counts: dict[str, Counter] = defaultdict(Counter)
    for _, _, label in domains[:TRAIN_N]:
        for word in words_of(label):
            for ctx, ch in trigrams(word):
                counts[ctx][ch] += 1

    vocab = len(ALPHABET) + 1
    model: dict[str, dict[str, float]] = {}
    for ctx, counter in counts.items():
        total = sum(counter.values())
        model[ctx] = {
            ch: round(math.log((n + 0.1) / (total + 0.1 * vocab)), 3)
            for ch, n in counter.items()
        }
    default_lp = {ctx: round(math.log(0.1 / (sum(c.values()) + 0.1 * vocab)), 3) for ctx, c in counts.items()}

    def score(word: str) -> float:
        total, n = 0.0, 0
        for ctx, ch in trigrams(word):
            table = model.get(ctx)
            if table is None:
                total += math.log(0.1 / (0.1 * vocab + 1))
            else:
                total += table.get(ch, default_lp[ctx])
            n += 1
        return total / max(n, 1)

    # Calibrate on domains the model did NOT train on.
    held = [
        w
        for _, _, label in domains[CALIBRATE_FROM:CALIBRATE_TO]
        for w in words_of(label)
        if len(w) >= 6
    ]
    scores = sorted(score(w) for w in held)
    threshold = scores[int(len(scores) * 0.02)]  # 2nd percentile of real words

    rng = random.Random(7)
    fake = ["".join(rng.choice(ALPHABET) for _ in range(rng.randint(6, 14))) for _ in range(2000)]
    caught = sum(score(w) < threshold for w in fake) / len(fake)
    print(f"words={len(held)} threshold={threshold:.3f} random-string-recall={caught:.2%}")

    (OUT / "lexical_model.json").write_text(
        json.dumps({"threshold": round(threshold, 3), "vocab": vocab, "model": model, "default": default_lp}, separators=(",", ":")),
        encoding="utf-8",
    )
    print("wrote", OUT)


if __name__ == "__main__":
    main()
