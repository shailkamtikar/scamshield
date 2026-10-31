import pytesseract
from PIL import Image

from app.config import settings


class OcrUnavailable(RuntimeError):
    """Tesseract is not installed or not configured."""


def extract_text_from_image(image_path: str) -> str:
    """
    Extract visible text from an image using Tesseract OCR.
    """

    if not settings.tesseract_cmd:
        raise OcrUnavailable(
            "Tesseract OCR is not installed. Install it or set TESSERACT_CMD."
        )

    pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

    image = Image.open(image_path)

    try:
        text = pytesseract.image_to_string(image)
    except pytesseract.TesseractNotFoundError as err:
        raise OcrUnavailable(
            "Tesseract OCR could not be started. Check TESSERACT_CMD."
        ) from err

    return text.strip()
