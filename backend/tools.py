"""
Mock tool functions available to the LangGraph nodes.

Both tools are deterministic and local-only — no external APIs, no real
calendar or CRM, no randomness — so demo runs are reproducible.
"""

import json
from pathlib import Path

_CRM_STORE_PATH = Path(__file__).parent / "data" / "crm_state.json"

# Canned "open slots" standing in for a real calendar. Deterministic:
# a given deal_id always gets the same slot back (cached below), and which
# slot a *new* deal_id receives depends only on how many distinct deals
# have been looked up so far — never on time or randomness.
_CALENDAR_SLOTS = [
    "Tue Sep 1, 10:00 AM",
    "Tue Sep 1, 2:00 PM",
    "Wed Sep 2, 11:00 AM",
    "Wed Sep 2, 3:30 PM",
]
_assigned_slots: dict[str, str] = {}


def calendar_lookup_tool(deal_id: str) -> str:
    """Look up the next open calendar slot for following up on a deal.

    Deterministic mock: pulls from a fixed in-memory list of canned slots.
    Repeated calls for the same deal_id return the same slot.
    """
    if deal_id not in _assigned_slots:
        slot = _CALENDAR_SLOTS[len(_assigned_slots) % len(_CALENDAR_SLOTS)]
        _assigned_slots[deal_id] = slot
    return _assigned_slots[deal_id]


def crm_write_tool(deal_id: str, new_status: str) -> dict:
    """Write an updated status to the flat-file CRM stand-in.

    Deterministic mock: persists {deal_id: new_status} into
    data/crm_state.json (created on first write) so status survives across
    requests during the demo, without any external CRM/DB.
    """
    store: dict[str, str] = {}
    if _CRM_STORE_PATH.exists():
        store = json.loads(_CRM_STORE_PATH.read_text())

    store[deal_id] = new_status
    _CRM_STORE_PATH.write_text(json.dumps(store, indent=2))

    return {"deal_id": deal_id, "status": new_status, "success": True}
