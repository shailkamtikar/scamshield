"""
Baselines and ablations for the report. Static: no network, no Gemini, no threat feeds, nothing is opened.

    uv run python scripts/eval_ablation.py [--json out.json]

Messages: what each kind of evidence contributes, by giving the engine less of the message.
  keyword baseline : a naive list of scam words (two or more hits = scam), no link checks
  links only       : the message is cut down to its links
  wording only     : the links are removed from the message
  wording + links  : the whole engine (offline rules)

Links: what each layer of the link engine contributes.
  lexical rules only            : trust registry and learned model switched off
  + trust registry              : official / popular / platform knowledge on
  + learned domain-name model   : everything that works without network (the default static mode)
"""

import argparse
import csv
import dataclasses
import json
import re
from pathlib import Path

from app.engine import url_analysis
from app.engine.analysis import Case, investigate_sync
from app.intel import trust
from app.intel.urls import extract_urls, parse_url

ROOT = Path(__file__).resolve().parents[2]
BENCH = ROOT / "data" / "benchmark"
FLAGGED = {"SUSPICIOUS", "DANGEROUS"}

KEYWORDS = [
    "urgent", "immediately", "verify", "kyc", "blocked", "suspended", "suspension", "otp", "pin", "password", "click", "prize", "won", "lottery",
    "refund", "claim", "expire", "expires", "update", "pay", "fee", "arrest", "job", "earn", "winner", "free", "offer", "limited", "account", "confirm",
    "congratulations", "bank", "link", "avoid", "legal", "action", "penalty", "reward", "cashback", "loan",
]


def keyword_flag(text: str) -> bool:
    words = set(re.findall(r"[a-z]+", text.lower()))
    return len(words & set(KEYWORDS)) >= 3


def wording_only(text: str) -> str:
    for u in extract_urls(text):
        text = text.replace(u.original, " ")
    return text


def links_only(text: str) -> str:
    return "\n".join(u.original for u in extract_urls(text))


def engine_flag(text: str) -> bool:
    if not text.strip():
        return False
    return investigate_sync(Case(text, network=False)).result["verdict"] in FLAGGED


def load_messages() -> dict[str, list[tuple[str, bool]]]:
    """(text, is_scam) per set. Sets that were used to tune the rules are marked."""
    sets = {}
    for name, file, note in (("handwritten", "messages_handwritten.csv", "used for tuning"), ("heldout", "messages_heldout.csv", "written later")):
        rows = list(csv.DictReader(open(BENCH / file, encoding="utf-8")))
        sets[f"{name} ({note})"] = [(r["text"], r["label"] == "scam") for r in rows]
    genuine = list(csv.DictReader(open(BENCH / "messages_genuine.csv", encoding="utf-8")))
    sets["genuine notices and ads (written later)"] = [(r["text"], False) for r in genuine]
    sealed = list(csv.DictReader(open(BENCH / "redteam_sealed.csv", encoding="utf-8")))
    rows = []
    for r in sealed:
        kinds = set(r["expected"].split("|"))
        if kinds & {"PHISHING", "FRAUD_SCAM", "MALICIOUS_CONTENT"} and not kinds & {"SAFE_TRANSACTIONAL", "SAFE_PROMOTIONAL", "SAFE_OTHER"}:
            rows.append((r["text"], True))
        elif kinds <= {"SAFE_TRANSACTIONAL", "SAFE_PROMOTIONAL", "SAFE_OTHER"}:
            rows.append((r["text"], False))  # spam-only and unclear rows are left out: they are a judgement call
    sets["sealed red-team (written later)"] = rows
    return sets


def score(pairs: list[tuple[bool, bool]]) -> dict:
    """pairs of (flagged, is_scam)."""
    tp = sum(f and s for f, s in pairs)
    fn = sum((not f) and s for f, s in pairs)
    fp = sum(f and not s for f, s in pairs)
    tn = sum((not f) and (not s) for f, s in pairs)
    det = tp / (tp + fn) if tp + fn else None
    fpr = fp / (fp + tn) if fp + tn else None
    precision = tp / (tp + fp) if tp + fp else None
    f1 = 2 * precision * det / (precision + det) if precision and det else (0.0 if det is not None and precision is not None else None)
    return {"tp": tp, "fn": fn, "fp": fp, "tn": tn, "detection": det, "false_alarm": fpr, "precision": precision, "f1": f1, "accuracy": (tp + tn) / max(len(pairs), 1), "n": len(pairs)}


def messages_report() -> dict:
    configs = {
        "Keyword baseline": keyword_flag,
        "Links only": lambda t: engine_flag(links_only(t)),
        "Wording only": lambda t: engine_flag(wording_only(t)),
        "Wording + links": engine_flag,
    }
    out = {}
    sets = load_messages()
    for cname, fn in configs.items():
        out[cname] = {sname: score([(fn(t), s) for t, s in rows]) for sname, rows in sets.items()}
        pooled = [(fn(t), s) for sname, rows in sets.items() if "written later" in sname for t, s in rows]
        out[cname]["the three later sets together"] = score(pooled)
    return out


def links_report() -> dict:
    rows = [r for r in csv.DictReader(open(BENCH / "urls.csv", encoding="utf-8")) if r["category"] != "malware_feed"]
    real_classify, real_risky = trust.classify, url_analysis.url_model.is_risky

    def unknown_only(parsed):
        info = real_classify(parsed)
        return dataclasses.replace(info, tier="UNKNOWN", brand=None, category=None, zone=None, rank=None, reason="")

    def run(split: str) -> dict:
        pairs = []
        for r in rows:
            if split != "all" and r["split"] != split:
                continue
            parsed = parse_url(r["url"])
            if parsed is None:
                pairs.append((True, r["label"] == "phish"))
                continue
            rep = url_analysis.analyze_url(parsed, network=False)
            if rep.verdict == "COULD_NOT_VERIFY":
                continue
            pairs.append((rep.verdict in FLAGGED, r["label"] == "phish"))
        return score(pairs)

    out = {}
    try:
        trust.classify = url_analysis.trust.classify = unknown_only
        url_analysis.url_model.is_risky = lambda domain: False
        out["Lexical rules only"] = {"all": run("all"), "test": run("test")}
        trust.classify = url_analysis.trust.classify = real_classify
        out["+ trust registry"] = {"all": run("all"), "test": run("test")}
        url_analysis.url_model.is_risky = real_risky
        out["+ learned domain-name model"] = {"all": run("all"), "test": run("test")}
    finally:
        trust.classify = url_analysis.trust.classify = real_classify
        url_analysis.url_model.is_risky = real_risky
    return out


def pct(v):
    return "  n/a" if v is None else f"{v * 100:5.1f}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    args = ap.parse_args()
    msg, links = messages_report(), links_report()
    print("MESSAGES (detection % / false alarms % / accuracy % / F1 %)")
    for cname, per in msg.items():
        print(f"\n{cname}")
        for sname, s in per.items():
            print(f"  {sname:40} n={s['n']:3}  det {pct(s['detection'])}  fp {pct(s['false_alarm'])}  acc {pct(s['accuracy'])}  f1 {pct(s['f1'])}")
    print("\nLINKS")
    for cname, per in links.items():
        for split, s in per.items():
            print(f"  {cname:30} {split:5} n={s['n']:4}  det {pct(s['detection'])}  fp {pct(s['false_alarm'])}  acc {pct(s['accuracy'])}  f1 {pct(s['f1'])}")
    if args.json:
        Path(args.json).write_text(json.dumps({"messages": msg, "links": links}, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
