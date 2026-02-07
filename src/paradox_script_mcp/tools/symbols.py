"""
Symbol listing tool
"""

from paradox_script.parser import parse_save_file

from paradox_script_mcp.core.game import GameContext


def list_symbols_tool(ctx: GameContext, file_path: str) -> str:
    """
    List symbols in a file (top level only)

    Args:
        ctx: The game context
        file_path: Relative path to the file

    Returns compact symbol listing for token efficiency.
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

    raw_data = data._data if hasattr(data, "_data") else data
    if not isinstance(raw_data, dict):
        return f"Error: Expected dict, got {type(raw_data).__name__}"

    lines = _format_generic(data, raw_data)

    return "\n".join(lines) if lines else f"No symbols found in {file_path}"


def _format_generic(data, raw_data: dict) -> list[str]:
    """Format data without known structure

    Args:
        data: Original ScriptData/ScriptNode with span info
        raw_data: The underlying dict (_data)
    """
    lines = []
    for key, value in raw_data.items():
        value_data = value._data if hasattr(value, "_data") else value

        # Get line info
        span = value.span if hasattr(value, "span") else None
        line_info = f"L{span[0]}-L{span[2]}" if span else ""

        if isinstance(value_data, dict):
            # Show block with id if present
            item_id = value_data.get("id", "")
            if item_id:
                lines.append(f"block: {key} ({line_info}, id={item_id})" if line_info else f"block: {key} (id={item_id})")
            else:
                lines.append(f"block: {key} ({line_info})" if line_info else f"block: {key}")
        elif isinstance(value_data, list):
            lines.append(f"list: {key} ({len(value_data)} items, {line_info})" if line_info else f"list: {key} ({len(value_data)} items)")
            for item in value_data:
                item_data = item._data if hasattr(item, "_data") else item
                if isinstance(item_data, dict):
                    item_id = item_data.get("id", "")
                    if item_id:
                        lines.append(f"  - {item_id}")
        else:
            # For primitive values, use key_span for single line
            key_pos = data.key_span(key) if hasattr(data, "key_span") else None
            val_line = f"L{key_pos[0]}" if key_pos else ""
            lines.append(f"value: {key} = {value_data} ({val_line})" if val_line else f"value: {key} = {value_data}")

    return lines
