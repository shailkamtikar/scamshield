from app.graph.graph import graph
from app.graph.state import ScamShieldState


initial_state = ScamShieldState(
    message="""
URGENT!

Your Microsoft account has been suspended.

Click here:

https://miconsoft-login.com

Call 9998269178 immediately.
""",
    claimed_organization="Microsoft",
)

result = graph.invoke(initial_state)

print(result)