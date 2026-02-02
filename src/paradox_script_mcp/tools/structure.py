"""
Structure inspection tool
"""

from typing import Any

from paradox_script.parser import parse_save_file

from paradox_script_mcp.core.game import GameContext


# Depth threshold: beyond this level, expand full content
EXPAND_DEPTH_THRESHOLD = 2


def get_structure_tool(
    ctx: GameContext, file_path: str, symbol: str, key_path: str | None = None
) -> str:
    """
    Get structure of a symbol (keys only, no full content)

    This is the key token-saving tool: shows what keys exist
    in a block without dumping the full script content.

    For deep nesting (3+ levels), returns full expanded content
    instead of [block] placeholders.

    Args:
        ctx: The game context
        file_path: Relative path to the file (required)
        symbol: Symbol name to inspect
        key_path: Optional dot-separated path to nested block
                 (e.g., "completion_reward.hidden_effect")

    Returns compact structure representation.
    """
    if not ctx.is_initialized:
        return "Error: Game not initialized. Call init_game first."

    full_path = ctx.resolve_path(file_path)
    if not full_path:
        return f"Error: File not found: {file_path}"

    try:
        data = parse_save_file(str(full_path))
    except Exception as e:
        return f"Error parsing {file_path}: {e}"

    # Find the symbol block
    block = _find_symbol_block(data, symbol)
    if block is None:
        return f"Symbol not found: {symbol} in {file_path}"

    # Navigate to nested block if key_path is specified
    display_name = symbol
    depth = 0
    if key_path:
        block = _navigate_key_path(block, key_path)
        if block is None:
            return f"Key path not found: {symbol}.{key_path}"
        display_name = f"{symbol}.{key_path}"
        depth = key_path.count(".") + 1

    # If depth >= threshold, expand fully
    expand_full = depth >= EXPAND_DEPTH_THRESHOLD

    return _format_structure(display_name, block, expand_full=expand_full)


def _find_symbol_block(data: Any, symbol: str) -> Any | None:
    """
    Find a symbol block in parsed data.

    Searches through various HOI4 structure patterns.
    """
    raw_data = data._data if hasattr(data, "_data") else data

    if not isinstance(raw_data, dict):
        return None

    # Direct top-level match
    if symbol in raw_data:
        return raw_data[symbol]

    # Search in focus_tree blocks (for focus IDs)
    if "focus_tree" in raw_data:
        result = _search_in_focus_tree(raw_data["focus_tree"], symbol)
        if result:
            return result

    # Search in event blocks (for event IDs)
    for event_type in ["country_event", "news_event"]:
        if event_type in raw_data:
            result = _search_in_events(raw_data[event_type], symbol)
            if result:
                return result

    # Search in achievement blocks
    if "achievement" in raw_data:
        result = _search_by_id(raw_data["achievement"], symbol)
        if result:
            return result

    # Generic search: look for blocks with matching id
    for key, value in raw_data.items():
        result = _search_by_id(value, symbol)
        if result:
            return result

    return None


def _search_in_focus_tree(tree_data: Any, symbol: str) -> Any | None:
    """Search for a focus or focus_tree by id"""
    if isinstance(tree_data, list):
        for tree in tree_data:
            result = _search_single_focus_tree(tree, symbol)
            if result:
                return result
    else:
        return _search_single_focus_tree(tree_data, symbol)
    return None


def _search_single_focus_tree(tree: Any, symbol: str) -> Any | None:
    """Search within a single focus_tree block"""
    tree_data = tree._data if hasattr(tree, "_data") else tree

    if not isinstance(tree_data, dict):
        return None

    # Check if the tree itself matches
    if tree_data.get("id") == symbol:
        return tree

    # Search in focus children
    if "focus" in tree_data:
        result = _search_by_id(tree_data["focus"], symbol)
        if result:
            return result

    return None


def _search_in_events(events: Any, symbol: str) -> Any | None:
    """Search for an event by id"""
    return _search_by_id(events, symbol)


def _search_by_id(data: Any, symbol: str) -> Any | None:
    """Search for a block with matching id"""
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


def _navigate_key_path(block: Any, key_path: str) -> Any | None:
    """
    Navigate to a nested block using dot-separated key path.

    Args:
        block: The starting block
        key_path: Dot-separated path (e.g., "completion_reward.hidden_effect")

    Returns:
        The nested block, or None if path not found.
    """
    current = block
    for key in key_path.split("."):
        # Unwrap ScriptNode if needed
        if hasattr(current, "_data"):
            current = current._data

        if not isinstance(current, dict):
            return None

        if key not in current:
            return None

        current = current[key]

    return current


def _format_structure(symbol: str, block: Any, expand_full: bool = False) -> str:
    """
    Format block structure compactly (keys only, no full content)

    Shows key names and value types, not actual values for blocks.
    If expand_full=True, expands all nested content instead of [block].
    """
    lines = [f"{symbol}:"]

    block_data = block._data if hasattr(block, "_data") else block

    # Handle list at top level
    if isinstance(block_data, list):
        if expand_full:
            return f"{symbol}:\n{_expand_value(block_data, indent=2)}"
        return f"{symbol}: [list] ({len(block_data)} items)"

    if not isinstance(block_data, dict):
        return f"{symbol}: {block_data}"

    for key, value in block_data.items():
        line = _format_key_value(key, value, expand_full=expand_full)
        lines.append(f"  {line}")

    return "\n".join(lines)


def _format_key_value(key: str, value: Any, expand_full: bool = False) -> str:
    """
    Format a single key-value pair compactly

    - Simple values: show the value
    - Blocks: show [block] with optional count (or expand if expand_full=True)
    - Lists: show count (or expand if expand_full=True)
    """
    # Unwrap ScriptNode if needed
    if hasattr(value, "_data"):
        value = value._data

    if isinstance(value, dict):
        if expand_full:
            return f"{key}:\n{_expand_value(value, indent=4)}"
        # Count effects/triggers inside
        count = len(value)
        return f"{key}: [block] ({count} keys)"

    elif isinstance(value, list):
        if len(value) == 0:
            return f"{key}: []"
        elif all(isinstance(v, (str, int, float, bool)) for v in value):
            # Simple list, show up to 3 items
            if len(value) <= 3:
                items = ", ".join(str(v) for v in value)
                return f"{key}: [{items}]"
            else:
                items = ", ".join(str(v) for v in value[:3])
                return f"{key}: [{items}, ...] ({len(value)} items)"
        else:
            if expand_full:
                return f"{key}:\n{_expand_value(value, indent=4)}"
            return f"{key}: [block list] ({len(value)} items)"

    elif isinstance(value, bool):
        return f"{key}: {'yes' if value else 'no'}"

    elif isinstance(value, (int, float)):
        return f"{key}: {value}"

    elif isinstance(value, str):
        # Truncate long strings
        if len(value) > 50:
            return f'{key}: "{value[:47]}..."'
        return f'{key}: "{value}"'

    else:
        return f"{key}: {type(value).__name__}"


def _expand_value(value: Any, indent: int = 0) -> str:
    """
    Recursively expand a value into readable format.
    Used when depth threshold is exceeded.
    """
    prefix = " " * indent

    # Unwrap ScriptNode if needed
    if hasattr(value, "_data"):
        value = value._data

    if isinstance(value, dict):
        lines = []
        for k, v in value.items():
            v_unwrapped = v._data if hasattr(v, "_data") else v
            if isinstance(v_unwrapped, (dict, list)):
                lines.append(f"{prefix}{k}:")
                lines.append(_expand_value(v_unwrapped, indent + 2))
            elif isinstance(v_unwrapped, bool):
                lines.append(f"{prefix}{k}: {'yes' if v_unwrapped else 'no'}")
            elif isinstance(v_unwrapped, str):
                lines.append(f'{prefix}{k}: "{v_unwrapped}"')
            else:
                lines.append(f"{prefix}{k}: {v_unwrapped}")
        return "\n".join(lines)

    elif isinstance(value, list):
        lines = []
        for i, item in enumerate(value):
            item_unwrapped = item._data if hasattr(item, "_data") else item
            if isinstance(item_unwrapped, (dict, list)):
                lines.append(f"{prefix}[{i}]:")
                lines.append(_expand_value(item_unwrapped, indent + 2))
            elif isinstance(item_unwrapped, bool):
                lines.append(f"{prefix}[{i}]: {'yes' if item_unwrapped else 'no'}")
            elif isinstance(item_unwrapped, str):
                lines.append(f'{prefix}[{i}]: "{item_unwrapped}"')
            else:
                lines.append(f"{prefix}[{i}]: {item_unwrapped}")
        return "\n".join(lines)

    elif isinstance(value, bool):
        return f"{prefix}{'yes' if value else 'no'}"

    elif isinstance(value, str):
        return f'{prefix}"{value}"'

    else:
        return f"{prefix}{value}"
