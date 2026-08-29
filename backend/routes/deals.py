"""
Route handlers for deal ingestion, listing, live-streaming triage, and
re-triage.

State lives in an in-memory dict, per deal_id — no DB, consistent with the
rest of the mocked stack. `/stream` is what actually (re-)invokes the graph;
`/retriage` only queues a new message + a flag, so the frontend can watch
the reclassification happen live by opening a fresh stream connection
afterward, rather than the POST racing a concurrent SSE push.
"""

import json
from datetime import date
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from graph import COMPILED_GRAPH, DealState, make_initial_state

router = APIRouter(prefix="/deals", tags=["deals"])

_DATA_PATH = Path(__file__).parent.parent / "data" / "synthetic_threads.json"

# In-memory stores, keyed by deal_id. _DEAL_META holds display-only fields
# (prospect_name/company) that live in the seed JSON but aren't part of the
# DealState schema itself.
_DEALS: dict[str, DealState] = {}
_DEAL_META: dict[str, dict] = {}

# Only these three carry the reasoning trace the frontend cares about —
# nested LLM sub-events (on_chat_model_*) inside analyst/strategist are
# filtered out to keep the stream at node granularity, per the design.
_TRACE_NODE_NAMES = {"analyst", "strategist", "sentry_check"}


class RetriageRequest(BaseModel):
    message: str


@router.post("/ingest")
async def ingest_deals() -> dict:
    """Load synthetic thread data and seed initial DealState per deal."""
    raw_deals = json.loads(_DATA_PATH.read_text())
    for entry in raw_deals:
        deal_id = entry["deal_id"]
        _DEALS[deal_id] = make_initial_state(deal_id, entry["thread_text"])
        _DEAL_META[deal_id] = {
            "prospect_name": entry.get("prospect_name"),
            "company": entry.get("company"),
        }
    return {"ingested": list(_DEALS.keys()), "count": len(_DEALS)}


@router.get("/{deal_id}/stream")
async def stream_deal(deal_id: str) -> EventSourceResponse:
    """Stream the graph's reasoning trace live via astream_events.

    This is what actually runs analyst -> strategist -> sentry_check for
    `deal_id`, using whatever is currently stored (a fresh ingest, or a
    thread updated by a prior /retriage call). Once a deal has reached
    max_iterations, this returns the stored final state as a single "done"
    event instead of re-invoking the graph — the router's iteration cap
    only guards the in-graph loop-back edge, so this is the explicit
    second check that stops a duplicate stream-open from burning another
    real classify pass.
    """
    state = _DEALS.get(deal_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"unknown deal_id {deal_id!r}")

    async def event_stream():
        current_state = state

        if current_state["iteration"] >= current_state["max_iterations"]:
            yield {"event": "done", "data": json.dumps(current_state)}
            return

        async for event in COMPILED_GRAPH.astream_events(
            current_state, version="v2", config={"recursion_limit": 10}
        ):
            if event["name"] not in _TRACE_NODE_NAMES:
                continue

            if event["event"] == "on_chain_start":
                yield {"event": "node_start", "data": json.dumps({"node": event["name"]})}

            elif event["event"] == "on_chain_end":
                output = event["data"].get("output")
                if isinstance(output, dict):
                    current_state = output
                yield {
                    "event": "node_end",
                    "data": json.dumps({"node": event["name"], "state": output}),
                }

        _DEALS[deal_id] = current_state
        yield {"event": "done", "data": json.dumps(current_state)}

    return EventSourceResponse(event_stream())


@router.post("/{deal_id}/retriage")
async def retriage_deal(deal_id: str, body: RetriageRequest) -> dict:
    """Inject a new message into the thread and flag it for re-triage.

    Does not invoke the graph itself — appends the message and sets
    retriage_requested=True on the stored state, then returns. The next
    GET /deals/{id}/stream call is what actually re-classifies, so the
    frontend can watch it happen live.
    """
    state = _DEALS.get(deal_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"unknown deal_id {deal_id!r}")

    if state["iteration"] >= state["max_iterations"]:
        return {
            "deal_id": deal_id,
            "queued": False,
            "reason": "max_iterations already reached for this deal",
        }

    # Assumes the injected message is from the prospect — the only kind of
    # "simulated new reply" the design describes.
    new_line = f"\n[{date.today().isoformat()}] Prospect: {body.message}"
    _DEALS[deal_id] = {
        **state,
        "thread_text": state["thread_text"] + new_line,
        "retriage_requested": True,
    }
    return {
        "deal_id": deal_id,
        "queued": True,
        "thread_text": _DEALS[deal_id]["thread_text"],
    }


@router.get("")
async def list_deals() -> list[dict]:
    """Current state snapshot for all deals (list view)."""
    return [
        {**_DEALS[deal_id], **_DEAL_META.get(deal_id, {})} for deal_id in sorted(_DEALS)
    ]
