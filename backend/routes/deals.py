"""
Route handlers for deal ingestion, streaming, and retriage.

All handlers are stubs — signatures and decorators are correct so the
app imports and the routes are registered, but nothing is implemented.
"""

from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse

router = APIRouter(prefix="/deals", tags=["deals"])


@router.post("/ingest")
async def ingest_deals() -> dict:
    """Ingest raw deal threads (e.g. synthetic_threads.json) into the system.

    TODO: implement
    """
    # TODO: implement
    return {}


@router.get("/{deal_id}/stream")
async def stream_deal(deal_id: str) -> EventSourceResponse:
    """Stream live trace/progress events for a deal via SSE.

    TODO: implement — wire this up to the LangGraph run for `deal_id`
    via astream_events(version="v2").
    """
    # TODO: implement
    async def event_stream():
        return
        yield  # pragma: no cover - makes this an async generator

    return EventSourceResponse(event_stream())


@router.post("/{deal_id}/retriage")
async def retriage_deal(deal_id: str) -> dict:
    """Re-run triage on a deal, optionally with a new operator message.

    TODO: implement
    """
    # TODO: implement
    return {}


@router.get("")
async def list_deals() -> list[dict]:
    """List all known deals and their current status.

    TODO: implement
    """
    # TODO: implement
    return []
