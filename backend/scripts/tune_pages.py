"""Measure page-inspection signals on the collected real pages (no network)."""

import json
from collections import Counter
from pathlib import Path

from app.intel import page
from app.intel.page import PageInfo
from app.intel.urls import parse_url

ROOT = Path(__file__).resolve().parents[2]


def main():
    rows = [json.loads(l) for l in open(ROOT / "data" / "raw" / "pages.jsonl", encoding="utf-8")]
    groups = {"phish": Counter(), "safe": Counter()}
    outcomes = {"phish": Counter(), "safe": Counter()}
    fetched = Counter()
    examples = []
    for r in rows:
        outcomes[r["label"]][r["outcome"]] += 1
        if "info" not in r:
            continue
        fetched[r["label"]] += 1
        info = PageInfo(**r["info"])
        info.forms = [{"action": f["action"], "inputs": [tuple(i) for i in f["inputs"]]} for f in info.forms]
        parsed = parse_url(r["final"]) or parse_url(r["url"])
        if parsed is None:
            continue
        ids = {s.id for s in page.analyze_info(parsed, info)}
        for i in ids:
            groups[r["label"]][i] += 1
        groups[r["label"]]["ANY_STRONG"] += bool(ids & {"HOST_FLAGGED_PAGE", "BRAND_MISMATCH_PAGE", "FORM_CROSS_DOMAIN", "APK_DOWNLOAD"})
        groups[r["label"]]["JS_ONLY"] += len(info.text) < 200 and not info.forms
        if r["label"] == "safe" and ids & {"HOST_FLAGGED_PAGE", "BRAND_MISMATCH_PAGE", "FORM_CROSS_DOMAIN", "APK_DOWNLOAD"}:
            examples.append((r["url"][:60], sorted(ids), info.title[:50]))
    for label in ("phish", "safe"):
        print(f"\n{label}: rows={sum(outcomes[label].values())} pages={fetched[label]}", dict(outcomes[label].most_common(5)))
        for k, v in groups[label].most_common():
            print(f"  {k:24} {v:4}  {v / max(fetched[label], 1):.1%}")
    print("\nsafe pages with a strong page signal:")
    for e in examples[:15]:
        print(" ", e)


if __name__ == "__main__":
    main()
