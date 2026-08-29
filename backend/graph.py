"""
LangGraph StateGraph definition for the Sentry deal-triage pipeline.

Defines the locked state schema and the three node stubs (analyst,
strategist, sentry_check) plus the graph wiring. No node logic or
feature-extraction is implemented yet — Phase 3 fills this in.
"""

from typing import Literal, Optional, TypedDict

from langgraph.graph import StateGraph


class DealFeatures(TypedDict):
    """Deterministic signals extracted from a deal thread (no LLM)."""

    days_since_last_message: int
    last_speaker: Literal["rep", "prospect"]
    last_commitment: Optional[str]
    commitment_date_passed: bool
    sentiment_delta: float  # -1..1
    unanswered_questions: int


class DealState(TypedDict):
    """Shared state threaded through every node in the graph."""

    deal_id: str
    thread_text: str
    features: Optional[DealFeatures]
    branch: Optional[Literal["confident", "ambiguous", "deprioritize"]]
    reasoning: Optional[str]
    draft: Optional[str]
    calendar_slot: Optional[str]
    crm_status: Optional[str]
    iteration: int
    max_iterations: int
    retriage_requested: bool


def analyst_node(state: DealState) -> DealState:
    """Extract deterministic features from the thread, then classify branch.

    TODO (Phase 3): run feature extraction (heuristics/regex, not an LLM
    call) to populate `state["features"]`, then call the LLM — constrained
    to the three branch labels — to set `state["branch"]` and a one-sentence
    `state["reasoning"]`.
    """
    # TODO: implement
    return state


def strategist_node(state: DealState) -> DealState:
    """Act on the classified branch.

    TODO (Phase 3): on "confident", call calendar_lookup_tool + draft a
    follow-up + crm_write_tool. On "ambiguous", surface the reasoning and
    draft nothing. On "deprioritize", log and take no action.
    """
    # TODO: implement
    return state


def sentry_check_node(state: DealState) -> DealState:
    """Bounded-loop gate: enforce max_iterations and route re-triage.

    TODO (Phase 3): increment/check `state["iteration"]` against
    `state["max_iterations"]` and decide whether to loop back to
    analyst_node (on `retriage_requested`) or end.
    """
    # TODO: implement
    return state


def build_graph() -> StateGraph:
    """Construct and compile the Sentry StateGraph.

    TODO (Phase 3): wire nodes/edges below, then compile with
    `recursion_limit=10` passed at invoke time as a backstop — the
    iteration counter in sentry_check_node is the primary cap
    (max_iterations = 2), this is a secondary safety net only.
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
    #     lambda state: "retriage" if state["retriage_requested"] else "END",
    #     {"retriage": "analyst", "END": "__end__"},
    # )

    return graph
