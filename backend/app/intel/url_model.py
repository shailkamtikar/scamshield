"""
Learned link model: a small logistic-regression classifier over the characters
of a domain name, trained by scripts/train_url_model.py on real phishing
domains versus ordinary sites. Inference is plain NumPy (no ML runtime).

It only ever RAISES suspicion on unknown domains, as one moderate signal.
"""

import json
import math
import re
import zlib
from functools import lru_cache
from pathlib import Path

import numpy as np

DATA = Path(__file__).parent / "data"
DIM = 1 << 17
_NUMERIC = DIM - 16  # last 16 slots hold hand-made numeric features


def _h(text: str) -> int:
    return zlib.crc32(text.encode("utf-8", "ignore")) % _NUMERIC


def features(domain: str) -> tuple[list[int], list[float]]:
    """Sparse feature vector for a registrable domain such as 'sbi-kyc.top'."""

    domain = domain.lower()
    label, _, suffix = domain.partition(".")
    counts: dict[int, float] = {}

    padded = f"^{label}$"
    for n in (2, 3, 4):
        for i in range(len(padded) - n + 1):
            k = _h(f"{n}:{padded[i : i + n]}")
            counts[k] = counts.get(k, 0.0) + 1.0
    norm = math.sqrt(sum(v * v for v in counts.values())) or 1.0
    counts = {k: v / norm for k, v in counts.items()}
    counts[_h(f"tld:{suffix}")] = 1.0

    letters = [c for c in label if c.isalpha()]
    vowels = sum(c in "aeiou" for c in letters)
    digits = sum(c.isdigit() for c in label)
    length = max(len(label), 1)
    probs = [label.count(c) / length for c in set(label)]
    numeric = [
        min(length / 30, 2.0),
        digits / length,
        label.count("-") / 4,
        vowels / max(len(letters), 1),
        -sum(p * math.log2(p) for p in probs) / 5,
        1.0 if re.search(r"\d", label) and re.search(r"[a-z]", label) else 0.0,
        1.0 if suffix.count(".") else 0.0,
    ]
    idx = list(counts.keys()) + [_NUMERIC + i for i in range(len(numeric))]
    val = list(counts.values()) + numeric
    return idx, val


@lru_cache(maxsize=1)
def _model():
    path = DATA / "url_model.npz"
    meta = DATA / "url_model_meta.json"
    if not path.exists() or not meta.exists():
        return None
    data = np.load(path)
    return data["weights"], float(data["bias"]), json.loads(meta.read_text(encoding="utf-8"))


def score(domain: str) -> float | None:
    """Raw model score (higher = more phishing-like); None if no model file."""
    model = _model()
    if model is None:
        return None
    weights, bias, _ = model
    idx, val = features(domain)
    return float(np.dot(weights[idx], np.asarray(val, dtype=np.float32)) + bias)


def is_risky(domain: str) -> bool:
    model = _model()
    value = score(domain)
    return bool(model and value is not None and value > model[2]["threshold_strict"])
