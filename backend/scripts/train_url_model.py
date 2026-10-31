"""
Train the learned link model (domain-name classifier).

Positive: domains from the Phishing.Database project (active phishing).
Negative: Tranco ranks 50k-1M (domains the trust list does NOT contain).
External test: OpenPhish domains (a different source) and a held-out Tranco
sample, so the score is not inflated by testing on the training source.

Only the domain name is used, never the path: safe samples are bare domains,
so path features would just learn "has a path = phishing".

    uv run --group dev python scripts/train_url_model.py
"""

import csv
import json
import random
from pathlib import Path

import numpy as np
import tldextract
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import roc_auc_score
from scipy.sparse import csr_matrix

from app.intel.registry_data import USER_CONTENT_PLATFORMS
from app.intel.url_model import DIM, features
from app.intel.trust import official_index

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
OUT = Path(__file__).resolve().parents[1] / "app" / "intel" / "data"
ext = tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)
rng = random.Random(5)


def registrable(host: str) -> str | None:
    host = host.strip().lower().rstrip(".")
    if not host or any(host == p or host.endswith("." + p) for p in USER_CONTENT_PLATFORMS):
        return None
    e = ext(host)
    return e.top_domain_under_public_suffix if e.suffix and e.domain else None


def matrix(domains: list[str]) -> csr_matrix:
    rows, cols, vals = [], [], []
    for i, d in enumerate(domains):
        idx, val = features(d)
        rows.extend([i] * len(idx))
        cols.extend(idx)
        vals.extend(val)
    return csr_matrix((vals, (rows, cols)), shape=(len(domains), DIM), dtype=np.float32)


def main():
    official = set(official_index())
    tranco = []
    with open(RAW / "top-1m.csv", newline="", encoding="utf-8") as fh:
        for rank, domain in csv.reader(fh):
            tranco.append((int(rank), domain.lower()))
    tranco_all = {d for _, d in tranco}

    phishdb = set()
    for line in open(RAW / "phishdb_domains.txt", encoding="utf-8", errors="ignore"):
        r = registrable(line)
        if r and r not in tranco_all and r not in official:
            phishdb.add(r)
    openphish = set()
    for line in open(RAW / "openphish.txt", encoding="utf-8", errors="ignore"):
        host = line.strip().split("//")[-1].split("/")[0].split(":")[0]
        r = registrable(host)
        if r and r not in tranco_all and r not in official:
            openphish.add(r)
    # The benchmark's phishing links must stay unseen too, so blind evaluation is fair.
    for row in csv.DictReader(open(ROOT / "data" / "benchmark" / "urls.csv", encoding="utf-8")):
        if row["label"] == "phish":
            host = row["url"].split("//")[-1].split("/")[0].split(":")[0]
            r = registrable(host)
            if r and r not in tranco_all and r not in official:
                openphish.add(r)
    phishdb -= openphish  # the external test must be unseen

    safe = [d for r, d in tranco if r > 50_000 and d not in official and d not in phishdb and d not in openphish]
    rng.shuffle(safe)
    phish = sorted(phishdb)
    rng.shuffle(phish)
    print(f"phishdb={len(phish)} openphish_test={len(openphish)} safe_pool={len(safe)}")

    n = min(len(phish), 120_000)
    train_pos, inner_pos = phish[: int(n * 0.9)], phish[int(n * 0.9) : n]
    train_neg, inner_neg, ext_neg = safe[: int(n * 0.9)], safe[int(n * 0.9) : n], safe[n : n + 40_000]

    X = matrix(train_pos + train_neg)
    y = np.array([1] * len(train_pos) + [0] * len(train_neg))
    clf = SGDClassifier(loss="log_loss", alpha=1e-6, max_iter=20, tol=1e-4, random_state=1)
    clf.fit(X, y)

    def scores(domains):
        return clf.decision_function(matrix(domains))

    s_in_pos, s_in_neg = scores(inner_pos), scores(inner_neg)
    s_ext_pos, s_ext_neg = scores(sorted(openphish)), scores(ext_neg)
    print(f"inner AUC    {roc_auc_score([1]*len(s_in_pos)+[0]*len(s_in_neg), np.r_[s_in_pos, s_in_neg]):.3f}")
    print(f"external AUC {roc_auc_score([1]*len(s_ext_pos)+[0]*len(s_ext_neg), np.r_[s_ext_pos, s_ext_neg]):.3f}")

    report = {}
    for fpr in (0.005, 0.01, 0.02, 0.05):
        t = float(np.quantile(s_ext_neg, 1 - fpr))
        rec = float((s_ext_pos > t).mean())
        report[str(fpr)] = {"threshold": round(t, 3), "recall_on_openphish": round(rec, 3)}
        print(f"  FP {fpr:.1%}: threshold {t:6.2f} catches {rec:.1%} of unseen OpenPhish domains")

    weights = clf.coef_[0].astype(np.float32)
    np.savez_compressed(OUT / "url_model.npz", weights=np.round(weights, 3), bias=np.float32(clf.intercept_[0]))
    (OUT / "url_model_meta.json").write_text(json.dumps({"threshold_strict": report["0.005"]["threshold"], "operating_points": report, "trained_on": len(train_pos) + len(train_neg)}, indent=1), encoding="utf-8")
    print("saved", (OUT / "url_model.npz").stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
