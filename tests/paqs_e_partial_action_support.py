"""Synthetic live-like shape, never a captured provider response."""

from typing import Any


def partial_actions() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = [
        {
            "type": "web_search_call",
            "status": "completed",
            "id": f"native-{i}",
            "opaque_restore_token": f"opaque-{i}",
            "action": {"type": "search", "queries": [f"query {i}-{j}" for j in range(4)]}
            if i < 6
            else {"type": "search" if i == 6 else "open_page" if i % 2 else "find_in_page"},
        }
        for i in range(16)
    ]
    for i, status in [(6, "incomplete"), (9, "failed"), (12, "in_progress")]:
        items[i]["status"] = status
        items[i]["action"].update(queries={"private-query": None}, sources="private-source")
    return items
