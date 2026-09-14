from app.graph.state import ScamShieldState
from app.services.ocr import extract_text_from_image


def screenshot_analysis_node(state: ScamShieldState) -> ScamShieldState:
    """
    Extract visible text from an uploaded screenshot.
    """

    if not state.image_path:
        return state

    extracted_text = extract_text_from_image(state.image_path)

    if extracted_text:
        state.evidence.append(
            f"Screenshot OCR text: {extracted_text}"
        )

    return state