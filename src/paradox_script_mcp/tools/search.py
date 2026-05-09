"""
Cross-file reference search tool
"""

import re

from paradox_script_mcp.core.game import GameContext


def search_references_tool(
    ctx: GameContext,
    query: str,
    glob_pattern: str = "**/*.txt",
    include_lines: bool = False,
) -> str:
    """
    Search for a string across all game script files.

    Scans files matching glob_pattern for occurrences of query.
    By default returns only file paths (token-efficient).
    Set include_lines=True to also return matching line numbers and content.

    Args:
        ctx: The game context
        query: String to search for (literal match)
        glob_pattern: Glob pattern relative to game directory (default: **/*.txt)
        include_lines: If True, include matching line numbers and content

    Returns:
        List of files (and optionally lines) containing the query.
    """
    if not ctx.is_initialized or ctx.game_directory is None:
        return "Error: Game not initialized. Call init_game first."

    game_dir = ctx.game_directory
    results: list[str] = []
    pattern = re.compile(re.escape(query))

    for path in sorted(game_dir.glob(glob_pattern)):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            continue

        if query not in text:
            continue

        rel = path.relative_to(game_dir).as_posix()

        if not include_lines:
            results.append(rel)
        else:
            matches = []
            for i, line in enumerate(text.splitlines(), start=1):
                if pattern.search(line):
                    matches.append(f"  L{i}: {line.strip()}")
            if matches:
                results.append(rel)
                results.extend(matches)

    if not results:
        return f"No matches found for: {query}"

    file_count = len([r for r in results if not r.startswith("  ")])
    header = f"Found in {file_count} file(s):"
    return header + "\n" + "\n".join(results)
