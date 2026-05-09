"""
Symbol listing tool
"""

from paradox_script.parser import parse_save_file

from paradox_script_mcp.core.game import GameContext


def find_symbol_at_line_tool(ctx: GameContext, file_path: str, line: int) -> str:
    """
    Find which symbol contains the given line number.

    Searches top-level blocks and list items (e.g. events, focuses).
    Returns the symbol name/ID and its line range so the caller can
    use get_structure to inspect it further.

    Args:
        ctx: The game context
        file_path: Relative path to the file
        line: Line number to look up (1-based)

    Returns:
        Symbol info: name, type, line range, and id if present.
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
        return "Error: Unexpected file structure"

    def get_span(obj: object) -> tuple[int, int, int, int] | None:
        raw = getattr(obj, "span", None)
        if raw is None:
            return None
        return (int(raw[0]), int(raw[1]), int(raw[2]), int(raw[3]))

    # Search top-level entries and list items within them
    for key, value in raw_data.items():
        top_span = get_span(value)
        value_data = value._data if hasattr(value, "_data") else value

        if isinstance(value_data, list):
            # e.g. country_event, focus (inside focus_tree), achievement
            for item in value_data:
                item_span = get_span(item)
                if item_span is None or not (item_span[0] <= line <= item_span[2]):
                    continue
                item_data = item._data if hasattr(item, "_data") else item
                item_id = item_data.get("id", "") if isinstance(item_data, dict) else ""
                name = item_data.get("name", "") if isinstance(item_data, dict) else ""
                label = item_id or name or "(unnamed)"
                return (
                    f"symbol: {label}\n"
                    f"  container: {key}\n"
                    f"  lines: L{item_span[0]}-L{item_span[2]}\n"
                    f'  use: get_structure(file_path, "{label}")'
                )
        elif isinstance(value_data, dict):
            # top-level block (e.g. achievement, focus_tree)
            if top_span is None or not (top_span[0] <= line <= top_span[2]):
                continue
            # Line is inside this top-level block.
            # First try to find a matching child list item (e.g. focus inside focus_tree)
            for child_key, child_val in value_data.items():
                child_data = (
                    child_val._data if hasattr(child_val, "_data") else child_val
                )
                if isinstance(child_data, list):
                    for item in child_data:
                        item_span = get_span(item)
                        if item_span is None or not (
                            item_span[0] <= line <= item_span[2]
                        ):
                            continue
                        item_data = item._data if hasattr(item, "_data") else item
                        item_id = (
                            item_data.get("id", "")
                            if isinstance(item_data, dict)
                            else ""
                        )
                        label = item_id or "(unnamed)"
                        return (
                            f"symbol: {label}\n"
                            f"  container: {key}.{child_key}\n"
                            f"  lines: L{item_span[0]}-L{item_span[2]}\n"
                            f'  use: get_structure(file_path, "{label}")'
                        )
            # No child matched — return the top-level block itself
            block_id = value_data.get("id", "")
            # Prefer string IDs (event/focus names); numeric IDs (achievement numbers) use key
            label = block_id if isinstance(block_id, str) and block_id else key
            return (
                f"symbol: {label}\n"
                f"  type: {key}\n"
                f"  lines: L{top_span[0]}-L{top_span[2]}\n"
                f'  use: get_structure(file_path, "{label}")'
            )

    # フォールバック: 最近傍シンボルを返す
    candidates = _collect_all_candidates(raw_data, get_span)
    nearest = _find_nearest_symbol(candidates, line)
    if nearest is not None:
        span = nearest["span"]
        if "type" in nearest:
            return (
                f"symbol: {nearest['label']}\n"
                f"  type: {nearest['type']}\n"
                f"  lines: L{span[0]}-L{span[2]}\n"
                f"  note: nearest symbol (line {line} is outside any block)\n"
                f"  use: {nearest['use']}"
            )
        return (
            f"symbol: {nearest['label']}\n"
            f"  container: {nearest['container']}\n"
            f"  lines: L{span[0]}-L{span[2]}\n"
            f"  note: nearest symbol (line {line} is outside any block)\n"
            f"  use: {nearest['use']}"
        )

    return f"No symbol found containing line {line} in {file_path}"


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


def _collect_all_candidates(raw_data: dict, get_span) -> list[dict]:
    """全シンボルを収集して返す（find_symbol_at_line のフォールバック用）"""
    results = []
    for key, value in raw_data.items():
        top_span = get_span(value)
        value_data = value._data if hasattr(value, "_data") else value

        if isinstance(value_data, list):
            for item in value_data:
                item_span = get_span(item)
                if item_span is None:
                    continue
                item_data = item._data if hasattr(item, "_data") else item
                item_id = item_data.get("id", "") if isinstance(item_data, dict) else ""
                name = item_data.get("name", "") if isinstance(item_data, dict) else ""
                label = item_id or name or "(unnamed)"
                results.append({
                    "label": label,
                    "container": key,
                    "span": item_span,
                    "use": f'get_structure(file_path, "{label}")',
                })

        elif isinstance(value_data, dict):
            if top_span is None:
                continue
            for child_key, child_val in value_data.items():
                child_data = child_val._data if hasattr(child_val, "_data") else child_val
                if isinstance(child_data, list):
                    for item in child_data:
                        item_span = get_span(item)
                        if item_span is None:
                            continue
                        item_data = item._data if hasattr(item, "_data") else item
                        item_id = (
                            item_data.get("id", "") if isinstance(item_data, dict) else ""
                        )
                        label = item_id or "(unnamed)"
                        results.append({
                            "label": label,
                            "container": f"{key}.{child_key}",
                            "span": item_span,
                            "use": f'get_structure(file_path, "{label}")',
                        })
            block_id = value_data.get("id", "")
            label = block_id if isinstance(block_id, str) and block_id else key
            results.append({
                "label": label,
                "type": key,
                "span": top_span,
                "use": f'get_structure(file_path, "{label}")',
            })
    return results


def _find_nearest_symbol(candidates: list[dict], line: int) -> dict | None:
    """指定行に最も近い開始行を持つシンボルを返す。同距離なら start <= line を優先。"""
    if not candidates:
        return None

    def sort_key(sym: dict) -> tuple[int, int]:
        start = sym["span"][0]
        return (abs(start - line), 0 if start <= line else 1)

    return min(candidates, key=sort_key)


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
                lines.append(
                    f"block: {key} ({line_info}, id={item_id})"
                    if line_info
                    else f"block: {key} (id={item_id})"
                )
            else:
                lines.append(
                    f"block: {key} ({line_info})" if line_info else f"block: {key}"
                )
        elif isinstance(value_data, list):
            lines.append(
                f"list: {key} ({len(value_data)} items, {line_info})"
                if line_info
                else f"list: {key} ({len(value_data)} items)"
            )
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
            lines.append(
                f"value: {key} = {value_data} ({val_line})"
                if val_line
                else f"value: {key} = {value_data}"
            )

    return lines
