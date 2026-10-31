"""
QR decoding. Tries zxing-cpp first (accurate, reads several codes), then
retries on enhanced / rotated copies of the image, then OpenCV as a last
resort. Pure image work: nothing is opened or fetched.
"""

import cv2
import numpy as np
import zxingcpp

MAX_SIDE = 2400


def _load(data: bytes) -> np.ndarray | None:
    arr = np.frombuffer(data, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return None
    h, w = img.shape[:2]
    if max(h, w) > MAX_SIDE:
        scale = MAX_SIDE / max(h, w)
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return img


def _variants(img: np.ndarray):
    yield img
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    yield gray
    h, w = gray.shape
    if max(h, w) < 900:
        yield cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(gray)
    yield clahe
    yield cv2.adaptiveThreshold(clahe, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 41, 8)
    yield cv2.bitwise_not(gray)
    blurred = cv2.GaussianBlur(gray, (0, 0), 2.0)
    yield cv2.addWeighted(gray, 1.8, blurred, -0.8, 0)  # sharpen
    for rot in (cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_180, cv2.ROTATE_90_COUNTERCLOCKWISE):
        yield cv2.rotate(gray, rot)


def decode_all(data: bytes) -> list[dict]:
    """Return every readable code as {text, format}. Empty list if none."""

    img = _load(data)
    if img is None:
        return []

    found: dict[str, str] = {}
    for variant in _variants(img):
        try:
            for result in zxingcpp.read_barcodes(variant):
                if result.valid and result.text:
                    found.setdefault(result.text, str(result.format))
        except Exception:  # noqa: BLE001
            continue
        if found:
            break

    if not found:
        detector = cv2.QRCodeDetector()
        for variant in _variants(img):
            try:
                text, _, _ = detector.detectAndDecode(variant)
            except cv2.error:
                continue
            if text:
                found[text.strip()] = "QRCode"
                break

    return [{"text": t, "format": f} for t, f in found.items()]


def decode_qr_code(image_path: str) -> str | None:
    """Backwards-compatible helper: first code in a file, or None."""
    with open(image_path, "rb") as fh:
        codes = decode_all(fh.read())
    return codes[0]["text"] if codes else None
