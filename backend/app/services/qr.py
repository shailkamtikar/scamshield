import cv2

_detector = cv2.QRCodeDetector()


def decode_qr_code(image_path: str) -> str | None:
    """
    Decode a QR code from an image file using OpenCV's built-in
    QRCodeDetector (no external system dependency required).

    Returns the decoded text/URL, or None if no QR code could be read.
    """

    image = cv2.imread(image_path)

    if image is None:
        return None

    data, _points, _straight_qrcode = _detector.detectAndDecode(image)

    return data.strip() or None
