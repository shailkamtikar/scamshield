from PIL import Image, ImageDraw

from app.services.ocr import extract_text_from_image


image_path = "test_screenshot.png"

image = Image.new("RGB", (1000, 300), "white")
draw = ImageDraw.Draw(image)

draw.text(
    (50, 50),
    "Microsoft Security Alert\nYour account has been suspended.\nClick here to verify immediately.",
    fill="black",
)

image.save(image_path)

text = extract_text_from_image(image_path)

print("OCR RESULT:")
print(text)