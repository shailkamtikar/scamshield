from app.graph.state import ScamShieldState
from app.graph.nodes.screenshot_analysis import screenshot_analysis_node


state = ScamShieldState(
    message="",
    image_path="test_screenshot.png",
)

result = screenshot_analysis_node(state)

print("SCREENSHOT EVIDENCE:")
for evidence in result.evidence:
    print(evidence)