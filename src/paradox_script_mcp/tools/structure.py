"""
Structure inspection tool
"""

import re
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

    # Find the symbol block via game plugin
    block = ctx.plugin.find_symbol_block(data, symbol)
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
        depth = key_path.count(".") + 1 + len(re.findall(r"\[\d+\]", key_path))

    # If depth >= threshold, expand fully
    expand_full = depth >= EXPAND_DEPTH_THRESHOLD

    return _format_structure(display_name, block, expand_full=expand_full)


def _navigate_key_path(block: Any, key_path: str) -> Any | None:
    """
    Navigate to a nested block using dot-separated key path.

    Supports list index access:
    - "option[0]" → key "option", then index 0
    - "option.0" → key "option", then segment "0" as index

    Args:
        block: The starting block
        key_path: Dot-separated path (e.g., "completion_reward.hidden_effect")

    Returns:
        The nested block, or None if path not found.
    """
    current = block
    for key in key_path.split("."):
        if hasattr(current, "_data"):
            current = current._data

        # List index access (e.g., "0", "1")
        if isinstance(current, list):
            try:
                idx = int(key)
                if 0 <= idx < len(current):
                    current = current[idx]
                    continue
                else:
                    return None
            except ValueError:
                return None

        if not isinstance(current, dict):
            return None

        # key[N] format (e.g., "option[0]")
        m = re.match(r"^(.+)\[(\d+)\]$", key)
        if m:
            dict_key, idx = m.group(1), int(m.group(2))
            if dict_key not in current:
                return None
            value = current[dict_key]
            if hasattr(value, "_data"):
                value = value._data
            if not isinstance(value, list) or idx >= len(value):
                return None
            current = value[idx]
        else:
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
        lines_list = [f"{symbol}: [list] ({len(block_data)} items)"]
        for i, item in enumerate(block_data):
            item_data = item._data if hasattr(item, "_data") else item
            if isinstance(item_data, dict):
                label = item_data.get("name", "") or item_data.get("id", "")
                if label:
                    lines_list.append(f"  [{i}]: {label}")
                else:
                    lines_list.append(f"  [{i}]")
        return "\n".join(lines_list)

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
            lines_list = [f"{key}: [block list] ({len(value)} items)"]
            for i, item in enumerate(value):
                item_data = item._data if hasattr(item, "_data") else item
                if isinstance(item_data, dict):
                    label = item_data.get("name", "") or item_data.get("id", "")
                    if label:
                        lines_list.append(f"    [{i}]: {label}")
                    else:
                        lines_list.append(f"    [{i}]")
            return "\n".join(lines_list)

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


def get_structure_by_id_tool(
    ctx: GameContext,
    symbol: str,
    glob_pattern: str = "**/*.txt",
    key_path: str | None = None,
) -> str:
    """
    IDでシンボルに直接ジャンプして構造を取得する。

    テキスト検索でファイルを絞り込んでから parse → find_symbol_block() で確認する。
    Stellarisのような大型ゲームでも効率的に動作する（パースはマッチしたファイルのみ）。

    Args:
        ctx: The game context
        symbol: Symbol ID to find (e.g., "shroud.4135", "end_of_the_cycle")
        glob_pattern: Glob pattern relative to game directory (default: **/*.txt)
        key_path: Optional dot-separated path to navigate into nested blocks

    Returns:
        Compact structure plus the source file path where the symbol was found.
    """
    if not ctx.is_initialized or ctx.game_directory is None:
        return "Error: Game not initialized. Call init_game first."

    game_dir = ctx.game_directory

    # フェーズ1: テキスト検索でファイルを絞り込む（パースなし、高速）
    candidate_paths = []
    for path in sorted(game_dir.glob(glob_pattern)):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue
        if symbol in text:
            candidate_paths.append(path)

    if not candidate_paths:
        return f"Symbol not found: {symbol!r} (no files contain this string)"

    # フェーズ2: 候補ファイルのみパースして定義ブロックを探す
    found_block = None
    found_file: str | None = None
    for path in candidate_paths:
        try:
            data = parse_save_file(str(path))
        except Exception:
            continue
        block = ctx.plugin.find_symbol_block(data, symbol)
        if block is not None:
            found_block = block
            found_file = path.relative_to(game_dir).as_posix()
            break

    if found_block is None or found_file is None:
        files_str = ", ".join(
            p.relative_to(game_dir).as_posix() for p in candidate_paths[:5]
        )
        suffix = f" (and {len(candidate_paths) - 5} more)" if len(candidate_paths) > 5 else ""
        return (
            f"Symbol '{symbol}' appears in {len(candidate_paths)} file(s) as text, "
            f"but no definition block found.\n"
            f"Files: {files_str}{suffix}\n"
            f"Tip: The symbol may be referenced but not defined in these files."
        )

    # フェーズ3: key_path ナビゲーション（get_structure_tool と同じロジック）
    display_name = symbol
    depth = 0
    if key_path:
        found_block = _navigate_key_path(found_block, key_path)
        if found_block is None:
            return f"Key path not found: {symbol}.{key_path} (found in {found_file})"
        display_name = f"{symbol}.{key_path}"
        depth = key_path.count(".") + 1 + len(re.findall(r"\[\d+\]", key_path))

    expand_full = depth >= EXPAND_DEPTH_THRESHOLD
    structure = _format_structure(display_name, found_block, expand_full=expand_full)
    return f"# found in: {found_file}\n{structure}"
