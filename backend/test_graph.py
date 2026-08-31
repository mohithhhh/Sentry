"""
Standalone local test for the compiled LangGraph pipeline — no FastAPI.

Invokes the graph directly against three of the Phase 2 synthetic deals and
prints the resulting DealState for each, so branching can be verified before
touching the API. Also simulates the signature "live re-triage" demo moment
on the ambiguous hero deal (deal-003): classify once, inject a new reply,
re-invoke, confirm it reclassifies to confident.

Run directly: python test_graph.py
Requires GOOGLE_API_KEY (see .env.example) — analyst_node makes a real
Gemini call.
"""

import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from graph import make_initial_state, run_graph  # noqa: E402  (after load_dotenv)

DEALS_PATH = "data/synthetic_threads.json"


def _load_deal(deal_id: str) -> dict:
    deals = json.load(open(DEALS_PATH))
    for d in deals:
        if d["deal_id"] == deal_id:
            return d
    raise KeyError(f"no deal with id {deal_id!r} in {DEALS_PATH}")


def _print_state(label: str, state: dict) -> None:
    print(f"\n=== {label} ===")
    print(json.dumps(state, indent=2))


def main() -> None:
    if not os.environ.get("GOOGLE_API_KEY"):
        print(
            "GOOGLE_API_KEY is not set — analyst_node calls Gemini directly "
            "and needs it. Copy .env.example to .env and fill it in.",
            file=sys.stderr,
        )
        sys.exit(1)

    # deal-001: unambiguous confident case.
    confident_deal = _load_deal("deal-001")
    confident_state = run_graph(
        make_initial_state(confident_deal["deal_id"], confident_deal["thread_text"])
    )
    _print_state("deal-001 (expect: confident)", confident_state)
    assert confident_state["branch"] == "confident"
    assert confident_state["draft"], "confident deals must produce a draft"
    assert confident_state["calendar_slot"]
    assert confident_state["crm_status"] == "confident"

    # deal-004: unambiguous deprioritize case.
    deprioritize_deal = _load_deal("deal-004")
    deprioritize_state = run_graph(
        make_initial_state(deprioritize_deal["deal_id"], deprioritize_deal["thread_text"])
    )
    _print_state("deal-004 (expect: deprioritize)", deprioritize_state)
    assert deprioritize_state["branch"] == "deprioritize"
    assert deprioritize_state["draft"] is None, "deprioritize must not draft anything"
    assert deprioritize_state["crm_status"] is None, "deprioritize must not touch the CRM"

    # deal-003: the ambiguous hero deal — classify once, then simulate the
    # live re-triage demo moment with a new reply and re-invoke.
    hero_deal = _load_deal("deal-003")
    hero_state = run_graph(make_initial_state(hero_deal["deal_id"], hero_deal["thread_text"]))
    _print_state("deal-003 (expect: ambiguous)", hero_state)
    assert hero_state["branch"] == "ambiguous"
    assert hero_state["draft"] is None, "ambiguous must not draft anything"
    assert hero_state["iteration"] == 1

    new_reply = (
        "\n[2026-08-29] Prospect: Sorry for the delay — we looped in our data "
        "lead and got sign-off. Would love to move forward, can we grab time "
        "this week to finalize pricing?"
    )
    retriage_input = {
        **hero_state,
        "thread_text": hero_state["thread_text"] + new_reply,
        "retriage_requested": True,
    }
    retriage_result = run_graph(retriage_input)
    _print_state("deal-003 after simulated retriage (expect: confident)", retriage_result)
    assert retriage_result["branch"] == "confident"
    assert retriage_result["draft"]
    assert retriage_result["iteration"] == 2, "one retriage pass should bring iteration to the cap"

    print("\nAll graph checks passed.")


if __name__ == "__main__":
    main()
