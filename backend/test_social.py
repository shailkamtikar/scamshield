from app.graph.state import ScamShieldState
from app.graph.nodes.social_engineering import social_engineering_node


state = ScamShieldState(
    message="""
URGENT!

Your Microsoft account has been suspended.

Click here immediately to verify your account.

If you do not act now, your account will be blocked.

Enter your password and OTP to restore access.
"""
)

result = social_engineering_node(state)

for evidence in result.evidence:
    print(evidence)