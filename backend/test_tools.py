"""
Standalone checks for tools.py — not a pytest suite, just enough to confirm
the mocked calendar/CRM tools behave deterministically.

Run directly: python test_tools.py
"""

from tools import calendar_lookup_tool, crm_write_tool


def main() -> None:
    # calendar_lookup_tool: same deal_id -> same slot, every time.
    slot_a = calendar_lookup_tool("deal-001")
    slot_a_again = calendar_lookup_tool("deal-001")
    assert slot_a == slot_a_again, "calendar_lookup_tool must be deterministic per deal_id"
    assert isinstance(slot_a, str) and slot_a, "calendar_lookup_tool must return a non-empty slot string"

    slot_b = calendar_lookup_tool("deal-002")
    assert slot_b != slot_a, "distinct deals should get distinct canned slots"
    print(f"calendar_lookup_tool('deal-001') -> {slot_a!r}")
    print(f"calendar_lookup_tool('deal-002') -> {slot_b!r}")

    # crm_write_tool: writes, returns a success receipt, and overwrites cleanly.
    result = crm_write_tool("deal-001", "confident")
    assert result == {"deal_id": "deal-001", "status": "confident", "success": True}
    print(f"crm_write_tool('deal-001', 'confident') -> {result}")

    result2 = crm_write_tool("deal-001", "closed")
    assert result2["status"] == "closed", "overwriting a deal's status must stick"
    print(f"crm_write_tool('deal-001', 'closed') -> {result2}")

    print("All tool checks passed.")


if __name__ == "__main__":
    main()
