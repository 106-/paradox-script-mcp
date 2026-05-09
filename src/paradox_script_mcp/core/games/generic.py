"""
Generic game plugin — fallback for unsupported games.

Searches for symbols by matching the `id` field across all top-level blocks.
Works for any Paradox game that uses `id` as the primary identifier.
"""

from __future__ import annotations

from typing import Any

from paradox_script_mcp.core.games import GamePlugin


class GenericPlugin(GamePlugin):
    """
    Fallback plugin for games without a dedicated implementation.

    Performs a generic id-based search across all top-level keys.
    """

    def find_symbol_block(self, data: Any, symbol: str) -> Any | None:
        raw_data = data._data if hasattr(data, "_data") else data
        if not isinstance(raw_data, dict):
            return None

        # Direct top-level match by key name
        if symbol in raw_data:
            return raw_data[symbol]

        # Search every top-level value for a block with matching id
        for value in raw_data.values():
            result = _search_by_id(value, symbol)
            if result is not None:
                return result

        return None


def _search_by_id(data: Any, symbol: str) -> Any | None:
    """Return the first block whose `id` field equals `symbol`."""
    if isinstance(data, list):
        for item in data:
            item_data = item._data if hasattr(item, "_data") else item
            if isinstance(item_data, dict) and item_data.get("id") == symbol:
                return item
    else:
        data_unwrapped = data._data if hasattr(data, "_data") else data
        if isinstance(data_unwrapped, dict) and data_unwrapped.get("id") == symbol:
            return data
    return None
