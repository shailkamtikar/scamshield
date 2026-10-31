"""
Rules-only explanation of one text file: no AI calls, no tokens used.

    uv run python scripts/explain_text.py path/to/file.txt [--net]
"""

import sys

from app.engine.analysis import Case, investigate_sync
from app.intel.trust import classify
from app.intel.urls import extract_urls

path = sys.argv[1]
text = open(path, encoding="utf-8").read()
net = "--net" in sys.argv

print("LINKS FOUND:")
for u in extract_urls(text):
    t = classify(u)
    print(f"  {u.original!r:60} -> {u.host_ascii} [{t.tier}{' ' + t.brand if t.brand else ''}]")

r = investigate_sync(Case(text, network=net)).result
print(f"\nVERDICT {r['verdict']} score={r['risk_score']} conf={r['confidence']} path={r['decision_path']}")
print("MESSAGE SIGNALS:")
for s in r["message_signals"]:
    print(f"  {s['id']:24} {s['points']:3} {s['strength']:8} {s['explanation'][:100]}")
for u in r["urls"]:
    print(f"LINK {u['url'][:70]} -> {u['verdict']} {u['score']}")
    for s in u["signals"]:
        print(f"     {s['id']:24} {s['points']:3} {s['strength']:8} {s['explanation'][:90]}")
