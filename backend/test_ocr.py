import pytesseract
from PIL import Image


pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


image = Image.new("RGB", (800, 200), "white")

text = pytesseract.image_to_string(image)

print("OCR test successful.")
print("Extracted text:", repr(text))