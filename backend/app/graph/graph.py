from app.graph.nodes.gemini_reasoning import gemini_reasoning_node
from langgraph.graph import StateGraph, START, END
from app.graph.state import ScamShieldState
from app.graph.nodes.extraction import extraction_node
from app.graph.nodes.url_investigation import url_investigation_node
from app.graph.nodes.identity_verification import identity_verification_node
from app.graph.nodes.social_engineering import social_engineering_node
from app.graph.nodes.risk_assessment import risk_assessment_node


builder = StateGraph(ScamShieldState)
builder.add_node("gemini_reasoning", gemini_reasoning_node)
builder.add_node("extraction", extraction_node)
builder.add_node("url_investigation", url_investigation_node)
builder.add_node("identity_verification", identity_verification_node)
builder.add_node("social_engineering", social_engineering_node)
builder.add_node("risk_assessment", risk_assessment_node)

builder.add_edge(START, "extraction")
builder.add_edge("extraction", "url_investigation")
builder.add_edge("url_investigation", "identity_verification")
builder.add_edge("identity_verification", "social_engineering")
# Deterministic scoring runs BEFORE Gemini so the reasoning layer can see
# the authoritative risk_score/score_breakdown and explain it, rather than
# the two being computed independently and potentially disagreeing.
builder.add_edge("social_engineering", "risk_assessment")
builder.add_edge("risk_assessment", "gemini_reasoning")
builder.add_edge("gemini_reasoning", END)

graph = builder.compile()