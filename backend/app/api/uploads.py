"""Shared validation for image uploads (screenshots and QR images)."""

import io

from fastapi import HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_PIXELS = 40_000_000
ALLOWED = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}

Image.MAX_IMAGE_PIXELS = MAX_PIXELS


async def read_image(file: UploadFile) -> tuple[bytes, str]:
    """Read and validate an uploaded image by its real content (not its name or declared type)."""

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image is too large (max 8 MB).")
    try:
        with Image.open(io.BytesIO(data)) as img:
            fmt = img.format or ""
            width, height = img.size
            img.verify()
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError):
        raise HTTPException(status_code=415, detail="Unsupported or corrupt image. Upload a PNG, JPEG or WEBP file.") from None
    if fmt not in ALLOWED:
        raise HTTPException(status_code=415, detail="Unsupported image type. Upload a PNG, JPEG or WEBP file.")
    if width * height > MAX_PIXELS:
        raise HTTPException(status_code=413, detail="Image dimensions are too large.")
    return data, ALLOWED[fmt]
