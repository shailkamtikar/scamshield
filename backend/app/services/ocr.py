import pytesseract
from PIL import Image


TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def extract_text_from_image(image_path: str) -> str:
    """
    Extract visible text from an image using Tesseract OCR.
    """

    image = Image.open(image_path)

    text = pytesseract.image_to_string(image)

    return text.strip()