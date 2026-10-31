"""Create SMS-style screenshots (light and dark mode) for testing the OCR path."""
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONTS = Path("C:/Windows/Fonts")


def shot(path, text, dark=False, w=720, sender="VK-SBIINB"):
    bg = (18, 18, 22) if dark else (245, 245, 247)
    fg = (235, 235, 240) if dark else (20, 20, 25)
    bubble = (45, 45, 52) if dark else (255, 255, 255)
    font = ImageFont.truetype(str(FONTS / "arial.ttf"), 30)
    bold = ImageFont.truetype(str(FONTS / "arialbd.ttf"), 30)
    lines = textwrap.wrap(text, 34)
    h = 140 + 44 * len(lines) + 60
    img = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(img)
    d.text((30, 30), sender, fill=fg, font=bold)
    d.rounded_rectangle((20, 100, w - 60, h - 30), 28, fill=bubble)
    for i, line in enumerate(lines):
        d.text((50, 125 + 44 * i), line, fill=fg, font=font)
    img.save(path)


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "../data/cache")
    out.mkdir(parents=True, exist_ok=True)
    shot(out / "shot_scam_light.png", "Dear customer, your SBI account will be blocked today. Update your KYC immediately at http://sbi-kyc-update.top/login or call 9876543210")
    shot(out / "shot_bank_dark.png", "Rs 1,200 debited from A/c XX1234 on 12-Mar to VPA store@okaxis. UPI Ref 123456789. Avl Bal Rs 5,000. - SBI", dark=True)
    shot(out / "shot_link_light.png", "Your order has shipped. Track it here https://www.amazon.in/gp/your-account/order-details", sender="AMAZON")
    print("written to", out)
