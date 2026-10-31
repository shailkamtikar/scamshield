"""
ScamShield investigation graph (LangGraph).

    extract -> message -> urls -> decide -> explain

Every node receives and returns the shared `Case`. Because each node is one
stage, `graph.stream(...)` yields real progress events for the UI.
"""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.engine import analysis, explain


class GraphState(TypedDict):
    case: analysis.Case


def _wrap(fn):
    def node(state: GraphState) -> GraphState:
        return {"case": fn(state["case"])}
    return node


builder = StateGraph(GraphState)
builder.add_node("extract", _wrap(analysis.step_extract))
builder.add_node("message", _wrap(analysis.step_message))
builder.add_node("urls", _wrap(analysis.step_urls))
builder.add_node("decide", _wrap(analysis.step_decide))
builder.add_node("explain", _wrap(explain.explain))

builder.add_edge(START, "extract")
builder.add_edge("extract", "message")
builder.add_edge("message", "urls")
builder.add_edge("urls", "decide")
builder.add_edge("decide", "explain")
builder.add_edge("explain", END)

graph = builder.compile()

STAGE_LABELS = {
    "extract": "Finding the links and details",
    "message": "Reading the wording for scam tricks",
    "urls": "Checking each link and page",
    "decide": "Weighing up the evidence",
    "explain": "Writing your report",
}


def run(case: analysis.Case) -> analysis.Case:
    return graph.invoke({"case": case})["case"]


def stream(case: analysis.Case):
    """Yield (node_name, case) after each stage completes."""
    for update in graph.stream({"case": case}, stream_mode="updates"):
        for name, value in update.items():
            yield name, value["case"]
