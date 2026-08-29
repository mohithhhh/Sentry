"""
LangGraph StateGraph definition for the Sentry deal-triage pipeline.

Defines the shared state shape and the node stubs that will eventually
analyze a deal, propose a strategy, and run a "sentry check" guardrail
pass before the graph terminates.

No node logic is implemented yet — this file only establishes the shape
of the graph so it can be built out incrementally.
"""

from typing import TypedDict

from langgraph.graph import StateGraph


class DealState(TypedDict):
    """Shared state threaded through every node in the graph.

    TODO: flesh out fields as the real pipeline takes shape. Placeholder
    fields below sketch the expected shape based on the deal-triage flow.
    """

    deal_id: str
    thread: list[dict]
    analysis: dict | None
    strategy: dict | None
    sentry_flags: list[str]
    status: str


def analyst_node(state: DealState) -> DealState:
    """Analyze the deal thread and populate `state["analysis"]`.

    TODO: implement — call out to an LLM to summarize/analyze the deal.
    """
    # TODO: implement
    return state


def strategist_node(state: DealState) -> DealState:
    """Propose a next-step strategy based on `state["analysis"]`.

    TODO: implement — call out to an LLM to draft a strategy/recommendation.
    """
    # TODO: implement
    return state


def sentry_check_node(state: DealState) -> DealState:
    """Run guardrail checks over the proposed strategy before it ships.

    TODO: implement — validate/flag risky recommendations.
    """
    # TODO: implement
    return state


def build_graph() -> StateGraph:
    """Construct and compile the Sentry StateGraph.

    TODO: implement — wire nodes and edges below once node logic exists.
    """
    graph = StateGraph(DealState)

    # TODO: graph.add_node("analyst", analyst_node)
    # TODO: graph.add_node("strategist", strategist_node)
    # TODO: graph.add_node("sentry_check", sentry_check_node)

    # TODO: graph.set_entry_point("analyst")
    # TODO: graph.add_edge("analyst", "strategist")
    # TODO: graph.add_edge("strategist", "sentry_check")

    # TODO: graph.add_conditional_edges(
    #     "sentry_check",
    #     lambda state: "END",  # placeholder routing function
    #     {"END": "__end__"},
    # )

    return graph
