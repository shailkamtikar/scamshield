"""
Measure the page-inspection sandbox on REAL pages.

For each link, download the HTML as TEXT ONLY through the guarded fetcher
(no JavaScript, no rendering, nothing written to disk, capped size, private
addresses blocked), run page inspection, and report what it found.
Uses phishing-feed links (never malware-download links) and unseen safe sites.

    uv run python scripts/measure_sandbox.py [--n 150]
"""

import argparse
import csv
import random
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from app.intel import net, page
from app.intel.urls import parse_url

ROOT = Path(__file__).resolve().parents[2]


def probe(url: str) -> dict:
    parsed = parse_url(url)
    if parsed is None:
        return {"url": url, "outcome": "UNPARSEABLE", "ids": [], "html": 0, "chain": 0}
    result = net.fetch(parsed.url, want_body=True, timeout=6.0)
    ids = [s.id for s in page.analyze(parsed, result.body)] if result.body else []
    info = page.parse_html(result.body) if result.body else None
    return {
        "url": url, "outcome": result.outcome, "ids": ids, "html": len(result.body), "chain": len(result.chain) - 1,
        "visible_text": len(info.text) if info else 0, "forms": len(info.forms) if info else 0,
        "title": (info.title.strip()[:50] if info else ""),
    }


def summarize(name: str, rows: list[dict]):
    outcomes = Counter(r["outcome"] for r in rows)
    fetched = [r for r in rows if r["html"]]
    flagged = [r for r in fetched if r["ids"]]
    thin = [r for r in fetched if r["visible_text"] < 200 and not r["forms"]]
    print(f"\n== {name}: n={len(rows)}")
    print("  outcomes        :", dict(outcomes.most_common()))
    print(f"  got HTML        : {len(fetched)}")
    print(f"  page flagged    : {len(flagged)} ({len(flagged) / max(len(fetched), 1):.0%} of pages fetched)")
    print(f"  thin/JS-only    : {len(thin)} (almost no visible text: the page needs a real browser)")
    print("  signals         :", dict(Counter(i for r in fetched for i in r["ids"]).most_common()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=150)
    ap.add_argument("--show", type=int, default=0)
    args = ap.parse_args()
    rng = random.Random(3)

    rows = list(csv.DictReader(open(ROOT / "data" / "benchmark" / "urls.csv", encoding="utf-8")))
    phish = [r["url"] for r in rows if r["category"] == "phishing_feed"]
    safe = [r["url"] for r in rows if r["category"] == "popular_unseen"]
    rng.shuffle(phish)
    rng.shuffle(safe)

    with ThreadPoolExecutor(max_workers=10) as pool:
        phish_rows = list(pool.map(probe, phish[: args.n]))
        safe_rows = list(pool.map(probe, safe[: args.n]))

    summarize("PHISHING FEED", phish_rows)
    summarize("UNSEEN SAFE SITES", safe_rows)
    for r in [x for x in phish_rows if x["html"] and not x["ids"]][: args.show]:
        print("  [phish not flagged]", r["url"][:70], "|", r["title"], "| text", r["visible_text"], "forms", r["forms"])
    for r in [x for x in safe_rows if x["ids"]][: args.show]:
        print("  [safe flagged]", r["url"][:70], r["ids"], "|", r["title"])


if __name__ == "__main__":
    main()
