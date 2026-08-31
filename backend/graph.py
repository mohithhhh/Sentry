"""
LangGraph StateGraph for the Sentry deal-triage pipeline.

Three nodes: analyst_node (deterministic feature extraction + LLM branch
classification), strategist_node (acts on "confident" only, calling the two
mock tools), sentry_check_node (bounded-loop gate). The LLM client is built
lazily (only when a node actually runs) so importing this module — or
compiling the graph — never requires GOOGLE_API_KEY to be set.
"""

import json
import re
from datetime import date
from functools import lru_cache
from typing import Literal, Optional, TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

from tools import calendar_lookup_tool, crm_write_tool


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


def make_initial_state(deal_id: str, thread_text: str) -> DealState:
    """Build a fresh DealState for a newly-ingested deal."""
    return {
        "deal_id": deal_id,
        "thread_text": thread_text,
        "features": None,
        "branch": None,
        "reasoning": None,
        "draft": None,
        "calendar_slot": None,
        "crm_status": None,
        "iteration": 0,
        "max_iterations": 2,
        "retriage_requested": False,
    }


# --- Deterministic feature extraction (heuristics/regex, no LLM) ----------

_LINE_RE = re.compile(r"^\[(\d{4}-\d{2}-\d{2})\]\s+(Rep|Prospect):\s*(.*)$")

# ponytail: keyword-lexicon sentiment, not a real sentiment model. Ceiling:
# misses negation/sarcasm/domain tone. Upgrade path: swap for a small
# LLM-scored sentiment call, or a proper sentiment model, if misclassifications
# show up in practice.
_POSITIVE_WORDS = {
    "great", "excited", "love", "loved", "solid", "appreciate", "promising",
    "yes", "perfect", "ready", "fantastic", "helpful", "genuinely", "works",
}
_NEGATIVE_WORDS = {
    "not", "however", "concern", "issue", "problem", "unfortunately",
    "delay", "no longer", "stop", "disappointed", "hesitant", "another",
}

# ponytail: keyword-triggered commitment detection, not real NLU. Ceiling:
# only catches commitments phrased with these markers. Upgrade path: an
# LLM extraction call if silent/implicit commitments turn out to matter.
_COMMITMENT_MARKERS = re.compile(
    r"\b(I'll|I will|We'll|We will|let me|let's|will send|will loop|"
    r"will get back|circle back|follow up|get back to you)\b",
    re.IGNORECASE,
)

# ponytail: relative-phrase date math, not real date parsing. Ceiling: only
# recognizes these specific phrases, and "passed" is a day-count heuristic
# rather than resolving an actual calendar date. Upgrade path: a date-parsing
# library (e.g. dateparser) if commitments start using varied phrasing.
_TIME_PHRASE_THRESHOLDS = [
    (re.compile(r"\btoday|tomorrow|eod\b", re.IGNORECASE), 2),
    (re.compile(r"\bthis week\b", re.IGNORECASE), 7),
    (re.compile(r"\bnext week\b", re.IGNORECASE), 14),
]
_DEFAULT_COMMITMENT_WINDOW_DAYS = 5


def _parse_thread(thread_text: str) -> list[tuple[date, str, str]]:
    """Parse '[YYYY-MM-DD] Rep|Prospect: text' lines into (date, speaker, text)."""
    parsed = []
    for line in thread_text.splitlines():
        match = _LINE_RE.match(line.strip())
        if not match:
            continue
        raw_date, speaker, text = match.groups()
        parsed.append((date.fromisoformat(raw_date), speaker, text))
    return parsed


def _sentiment_score(text: str) -> float:
    words = re.findall(r"[a-zA-Z']+", text.lower())
    pos = sum(1 for w in words if w in _POSITIVE_WORDS)
    neg = sum(1 for w in words if w in _NEGATIVE_WORDS)
    return max(-1.0, min(1.0, (pos - neg) * 0.3))


def _find_last_commitment(parsed: list[tuple[date, str, str]]) -> Optional[str]:
    for _, _, text in reversed(parsed):
        if _COMMITMENT_MARKERS.search(text):
            # Return the sentence containing the marker, not the whole message.
            for sentence in re.split(r"(?<=[.!?])\s+", text):
                if _COMMITMENT_MARKERS.search(sentence):
                    return sentence.strip()
    return None


def _commitment_date_passed(commitment: Optional[str], days_since: int) -> bool:
    if not commitment:
        return False
    for pattern, threshold_days in _TIME_PHRASE_THRESHOLDS:
        if pattern.search(commitment):
            return days_since >= threshold_days
    return days_since >= _DEFAULT_COMMITMENT_WINDOW_DAYS


def extract_features(thread_text: str) -> DealFeatures:
    """Deterministically extract DealFeatures from raw thread text.

    No LLM call — pure heuristics/regex over the parsed thread, per the
    hybrid-judgment design (this keeps the reasoning trace inspectable
    instead of relying on the LLM to eyeball raw text for these signals).
    """
    parsed = _parse_thread(thread_text)
    if not parsed:
        # Malformed/empty thread — safe, inert defaults.
        return {
            "days_since_last_message": 0,
            "last_speaker": "prospect",
            "last_commitment": None,
            "commitment_date_passed": False,
            "sentiment_delta": 0.0,
            "unanswered_questions": 0,
        }

    last_date, last_speaker_raw, last_text = parsed[-1]
    # ponytail: wall-clock "today", not a fixed simulated demo date. Ceiling:
    # day-counts drift as real time passes since the synthetic data was
    # written. Upgrade path: a SENTRY_TODAY env override if a demo runs long
    # after the thread dates were authored.
    days_since_last_message = (date.today() - last_date).days

    last_commitment = _find_last_commitment(parsed)

    prospect_messages = [text for _, speaker, text in parsed if speaker == "Prospect"]
    if len(prospect_messages) >= 2:
        sentiment_delta = _sentiment_score(prospect_messages[-1]) - _sentiment_score(
            prospect_messages[-2]
        )
        sentiment_delta = max(-1.0, min(1.0, sentiment_delta))
    else:
        sentiment_delta = 0.0

    return {
        "days_since_last_message": days_since_last_message,
        "last_speaker": "rep" if last_speaker_raw == "Rep" else "prospect",
        "last_commitment": last_commitment,
        "commitment_date_passed": _commitment_date_passed(
            last_commitment, days_since_last_message
        ),
        "sentiment_delta": sentiment_delta,
        # ponytail: counts literal "?" in the last message only. Ceiling:
        # misses implicit questions phrased without one ("let us know if
        # that's realistic"), and any earlier unanswered question the
        # thread moved past. Upgrade path: LLM-based question extraction
        # across the whole thread if this undercount matters in practice.
        "unanswered_questions": last_text.count("?"),
    }


# --- LLM client (lazy — never constructed at import/compile time) ---------


@lru_cache(maxsize=1)
def _get_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=0)


class _ClassificationResult(BaseModel):
    branch: Literal["confident", "ambiguous", "deprioritize"]
    reasoning: str = Field(
        description=(
            "One sentence naming the specific signal(s) that drove this "
            "classification."
        )
    )


@lru_cache(maxsize=1)
def _get_classifier():
    return _get_llm().with_structured_output(_ClassificationResult)


_BRANCH_DEFINITIONS = """\
- confident: clear signal the deal needs action now (recent momentum, an \
explicit ask, or a live commitment with time pressure).
- ambiguous: genuinely unclear — e.g. positive momentum followed by \
unexplained silence, or cooling signals with no stated objection. Do not \
guess; if the reason for stalling isn't evident, this is the label.
- deprioritize: the prospect has explicitly disengaged (declined, chose a \
competitor, or asked to stop being contacted).\
"""


def _build_classification_prompt(thread_text: str, features: DealFeatures) -> str:
    return (
        "You are triaging a single sales deal thread. Classify it into "
        f"exactly one of three branches:\n{_BRANCH_DEFINITIONS}\n\n"
        "Extracted signals (already computed deterministically — trust "
        "these over your own read of tone):\n"
        f"{json.dumps(features, indent=2)}\n\n"
        f"Full thread for context:\n{thread_text}\n\n"
        "Classify the branch and give a one-sentence reasoning that names "
        "the specific signal(s) that drove the decision."
    )


def analyst_node(state: DealState) -> DealState:
    """Extract deterministic features, then classify the branch via LLM."""
    features = extract_features(state["thread_text"])
    prompt = _build_classification_prompt(state["thread_text"], features)
    result: _ClassificationResult = _get_classifier().invoke(prompt)
    return {
        **state,
        "features": features,
        "branch": result.branch,
        "reasoning": result.reasoning,
        # This pass has now consumed any pending retriage request.
        "retriage_requested": False,
    }


def _draft_followup(state: DealState, calendar_slot: str) -> str:
    prompt = (
        "Write a short, warm, specific 2-4 sentence follow-up email to the "
        "prospect in this deal thread. Reference concrete context from the "
        "thread and propose the given time slot for a call. No subject "
        "line, no generic filler — just the message body.\n\n"
        f"Deal thread:\n{state['thread_text']}\n\n"
        f"Why this deal needs action now: {state['reasoning']}\n"
        f"Proposed time slot: {calendar_slot}\n"
    )
    response = _get_llm().invoke(prompt)
    return _content_to_text(response.content)


def _content_to_text(content: str | list) -> str:
    """Normalize a LangChain message's .content into a plain string.

    Some providers/models (observed with gemini-3.5-flash-lite) return a
    list of content-block dicts (e.g. [{"type": "text", "text": "..."}])
    instead of a bare string. DealState.draft and the frontend both expect
    plain text, so every caller routes through here rather than trusting
    .content's shape.
    """
    if isinstance(content, str):
        return content
    return "".join(
        block.get("text", "") if isinstance(block, dict) else str(block)
        for block in content
    )


def strategist_node(state: DealState) -> DealState:
    """Act on the classified branch.

    Only "confident" calls any tool — the calendar lookup and the CRM
    write — and drafts a follow-up. "ambiguous" surfaces the reasoning
    analyst_node already produced and drafts nothing; "deprioritize" logs
    via that same reasoning and takes no action. Neither of the other two
    branches touches a tool, by design — that restraint is the point.
    """
    if state["branch"] != "confident":
        return state

    slot = calendar_lookup_tool(state["deal_id"])
    draft = _draft_followup(state, slot)
    crm_result = crm_write_tool(state["deal_id"], "confident")
    return {
        **state,
        "calendar_slot": slot,
        "draft": draft,
        "crm_status": crm_result["status"],
    }


def sentry_check_node(state: DealState) -> DealState:
    """Record that one classify+strategize cycle just completed.

    The stop/loop decision itself lives in `_route_after_sentry_check` so
    the cap is enforced by an explicit, separately-testable function
    rather than buried in a node body.
    """
    return {**state, "iteration": state["iteration"] + 1}


def _route_after_sentry_check(state: DealState) -> Literal["retriage", "end"]:
    """Bounded-loop router: forces "end" once max_iterations is hit,
    regardless of model output or retriage_requested. `recursion_limit=10`
    (applied in run_graph) is a secondary backstop only — never relied on
    alone.
    """
    if state["iteration"] >= state["max_iterations"]:
        return "end"
    if state["retriage_requested"]:
        return "retriage"
    return "end"


def build_graph() -> StateGraph:
    """Construct (but do not compile) the Sentry StateGraph."""
    graph = StateGraph(DealState)

    graph.add_node("analyst", analyst_node)
    graph.add_node("strategist", strategist_node)
    graph.add_node("sentry_check", sentry_check_node)

    graph.set_entry_point("analyst")
    graph.add_edge("analyst", "strategist")
    graph.add_edge("strategist", "sentry_check")

    graph.add_conditional_edges(
        "sentry_check",
        _route_after_sentry_check,
        {"retriage": "analyst", "end": END},
    )

    return graph


COMPILED_GRAPH = build_graph().compile()


def run_graph(state: DealState) -> DealState:
    """Invoke the compiled graph with the recursion_limit backstop always
    applied — see the module docstring and _route_after_sentry_check for
    why this is a secondary net, not the primary bounded-loop mechanism.
    """
    return COMPILED_GRAPH.invoke(state, config={"recursion_limit": 10})
