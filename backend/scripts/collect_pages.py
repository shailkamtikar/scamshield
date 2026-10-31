"""
Collect parsed page features from real sites for calibrating page inspection.

Pages are fetched as TEXT through the guarded fetcher; no JavaScript runs.
Only extracted features (title, form fields, visible text excerpt) are kept in
data/raw/pages.jsonl (git-ignored). Raw HTML is never written to disk.
Malware-download links are not used.

    uv run python scripts/collect_pages.py [--n 300]
"""

import argparse
import csv
import json
import random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.intel import net, page
from app.intel.trust import classify
from app.intel.urls import parse_url

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "raw" / "pages.jsonl"


def probe(item):
    url, label, category = item
    parsed = parse_url(url)
    if parsed is None:
        return None
    result = net.fetch(parsed.url, want_body=True, timeout=6.0)
    row = {"url": url, "label": label, "category": category, "outcome": result.outcome, "final": result.final_url}
    if result.body:
        row["info"] = page.parse_html(result.body).to_dict()
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300)
    args = ap.parse_args()
    rng = random.Random(11)

    phish = [l.strip() for l in (ROOT / "data" / "raw" / "openphish.txt").read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = list(csv.DictReader(open(ROOT / "data" / "benchmark" / "urls.csv", encoding="utf-8")))
    phish += [r["url"] for r in rows if r["category"] == "phishing_feed"]
    phish = sorted(set(phish))
    safe = [r["url"] for r in rows if r["category"] in {"popular_unseen", "login_path_on_real_site"}]
    rng.shuffle(phish)
    rng.shuffle(safe)
    work = [(u, "phish", "phishing_feed") for u in phish[: args.n]] + [(u, "safe", "popular_unseen") for u in safe[: args.n]]
    work = [w for w in work if (p := parse_url(w[0])) and classify(p).tier != "OFFICIAL"]

    with ThreadPoolExecutor(max_workers=12) as pool, open(OUT, "w", encoding="utf-8") as fh:
        for i, row in enumerate(pool.map(probe, work)):
            if row:
                fh.write(json.dumps(row) + "\n")
            if i % 100 == 0:
                print(i, flush=True)
    print("done", OUT)


if __name__ == "__main__":
    main()
