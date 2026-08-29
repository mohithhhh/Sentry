"""
Tool functions available to the LangGraph nodes.

These are plain Python functions (not yet wrapped as LangChain/LangGraph
tools) that will eventually hit a calendar API and a CRM. For now they
return placeholder values so callers can be wired up before the real
integrations exist.
"""


def calendar_lookup_tool(deal_id: str) -> dict:
    """Look up upcoming calendar events related to a deal.

    TODO: implement — call the calendar API/integration.

    Args:
        deal_id: Identifier of the deal to look up events for.

    Returns:
        Placeholder dict until implemented.
    """
    # TODO: implement
    return {"deal_id": deal_id, "events": []}


def crm_write_tool(deal_id: str, new_status: str) -> dict:
    """Write an updated status back to the CRM for a given deal.

    TODO: implement — call the CRM API/integration.

    Args:
        deal_id: Identifier of the deal to update.
        new_status: The new status to write.

    Returns:
        Placeholder dict until implemented.
    """
    # TODO: implement
    return {"deal_id": deal_id, "status": new_status, "success": False}
