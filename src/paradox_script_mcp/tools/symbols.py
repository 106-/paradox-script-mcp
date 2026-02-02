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

    lines = _format_generic(raw_data)

    return "\n".join(lines) if lines else f"No symbols found in {file_path}"


def _format_generic(data: dict) -> list[str]:
    """Format data without known structure"""
    lines = []
    for key, value in data.items():
        value_data = value._data if hasattr(value, "_data") else value

        if isinstance(value_data, dict):
            # Show block with id if present
            item_id = value_data.get("id", "")
            if item_id:
                lines.append(f"block: {key} (id={item_id})")
            else:
                lines.append(f"block: {key}")
        elif isinstance(value_data, list):
            lines.append(f"list: {key} ({len(value_data)} items)")
        else:
            lines.append(f"value: {key} = {value_data}")

    return lines
