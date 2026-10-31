"""
Screenshot text extraction: image clean-up + Tesseract, scored by the
engine's own word-confidence so the best reading wins.
"""

import re
from dataclasses import dataclass

import cv2
import numpy as np
import pytesseract

from app.config import settings


class OcrUnavailable(RuntimeError):
    """Tesseract is not installed or not configured."""


@dataclass
class OcrResult:
    text: str
    confidence: float  # mean word confidence 0-100
    words: int


def _prepare(img: np.ndarray) -> list[np.ndarray]:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    if w < 1400:
        scale = 1600 / w
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    if gray.mean() < 120:  # dark mode: light text on dark background
        gray = cv2.bitwise_not(gray)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
    _, otsu = cv2.threshold(clahe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return [gray, otsu]


def _read(img: np.ndarray, lang: str) -> OcrResult:
    data = pytesseract.image_to_data(img, lang=lang, config="--psm 6", output_type=pytesseract.Output.DICT)
    confs, words, lines = [], [], {}
    for i, word in enumerate(data["text"]):
        word = word.strip()
        try:
            conf = float(data["conf"][i])
        except (TypeError, ValueError):
            continue
        if not word or conf < 0:
            continue
        confs.append(conf)
        words.append(word)
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        lines.setdefault(key, []).append(word)
    text = "\n".join(" ".join(ws) for _, ws in sorted(lines.items()))
    return OcrResult(text.strip(), float(np.mean(confs)) if confs else 0.0, len(words))


def extract_text(data: bytes) -> OcrResult:
    if not settings.tesseract_cmd:
        raise OcrUnavailable("Tesseract OCR is not installed. Install it or set TESSERACT_CMD.")
    pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return OcrResult("", 0.0, 0)

    try:
        langs = pytesseract.get_languages(config="")
        lang = "eng+hin" if "hin" in langs else "eng"
        best = OcrResult("", 0.0, 0)
        for variant in _prepare(img):
            result = _read(variant, lang)
            if result.words and result.confidence * min(result.words, 30) > best.confidence * min(best.words, 30):
                best = result
        return best
    except pytesseract.TesseractNotFoundError as err:
        raise OcrUnavailable("Tesseract OCR could not be started. Check TESSERACT_CMD.") from err


def extract_text_from_image(image_path: str) -> str:
    """Helper for scripts: text of an image file."""
    with open(image_path, "rb") as fh:
        return extract_text(fh.read()).text


def repair_url_text(text: str) -> str:
    """Fix common OCR slips that only matter inside links (e.g. 'https //', 'hftps')."""
    out = re.sub(
        r"\bh[tf]{1,2}ps?\s*[:;]\s*/\s*/",
        lambda m: "https://" if "s" in m.group(0).lower() else "http://",
        text,
        flags=re.I,
    )
    out = re.sub(r"(?i)\b(https?://)\s+", r"\1", out)
    # A link wrapped onto the next line: join it back together.
    return re.sub(r"(?i)(https?://\S*[-./_=?&])[ \t]*\r?\n[ \t]*(\S)", r"\1\2", out)
