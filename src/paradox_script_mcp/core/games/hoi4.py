"""
HOI4-specific game plugin.

Provides optimized symbol search for Hearts of Iron IV script structures:
- focus_tree / focus
- country_event / news_event
- achievement
Falls back to generic id-based search for other block types.
"""

from __future__ import annotations

from typing import Any

from paradox_script_mcp.core.games import GamePlugin
from paradox_script_mcp.core.games.generic import _search_by_id


class Hoi4Plugin(GamePlugin):
    """Plugin for Hearts of Iron IV."""

    def find_symbol_block(self, data: Any, symbol: str) -> Any | None:
        raw_data = data._data if hasattr(data, "_data") else data
        if not isinstance(raw_data, dict):
            return None

        # Direct top-level match by key name
        if symbol in raw_data:
            return raw_data[symbol]

        # Search in focus_tree blocks (for focus IDs)
        if "focus_tree" in raw_data:
            result = _search_in_focus_tree(raw_data["focus_tree"], symbol)
            if result is not None:
                return result

        # Search in event blocks (for event IDs)
        for event_type in ["country_event", "news_event"]:
            if event_type in raw_data:
                result = _search_by_id(raw_data[event_type], symbol)
                if result is not None:
                    return result

        # Search in achievement blocks
        if "achievement" in raw_data:
            result = _search_by_id(raw_data["achievement"], symbol)
            if result is not None:
                return result

        # Generic fallback: search every top-level value by id
        for value in raw_data.values():
            result = _search_by_id(value, symbol)
            if result is not None:
                return result

        return None


def _search_in_focus_tree(tree_data: Any, symbol: str) -> Any | None:
    if isinstance(tree_data, list):
        for tree in tree_data:
            result = _search_single_focus_tree(tree, symbol)
            if result is not None:
                return result
    else:
        return _search_single_focus_tree(tree_data, symbol)
    return None


def _search_single_focus_tree(tree: Any, symbol: str) -> Any | None:
    tree_data = tree._data if hasattr(tree, "_data") else tree
    if not isinstance(tree_data, dict):
        return None

    # Check if the tree itself matches
    if tree_data.get("id") == symbol:
        return tree

    # Search in focus children
    if "focus" in tree_data:
        result = _search_by_id(tree_data["focus"], symbol)
        if result is not None:
            return result

    return None
