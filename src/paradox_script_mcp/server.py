"""
Paradox Script MCP Server

Main entry point for the MCP server.
Provides tools for efficient discovery of HOI4 game scripts.
"""

from mcp.server.fastmcp import FastMCP

from paradox_script_mcp.core.game import GameContext
from paradox_script_mcp.tools.explore import list_directories_tool, list_files_tool
from paradox_script_mcp.tools.search import search_references_tool
from paradox_script_mcp.tools.symbols import find_symbol_at_line_tool, list_symbols_tool
from paradox_script_mcp.tools.structure import get_structure_by_id_tool, get_structure_tool

# Global game context instance
_ctx = GameContext()

# Create MCP server
mcp = FastMCP("paradox-script")


@mcp.tool()
def init_game(game_directory: str) -> str:
    """
    Initialize the MCP server with a HOI4 game directory.

    This sets the game directory path for subsequent operations.
    Call this first before using other tools.

    Args:
        game_directory: Path to the HOI4 game directory
                       (e.g., "/path/to/Hearts of Iron IV")

    Returns:
        Status message confirming initialization.
    """
    try:
        _ctx.initialize(game_directory)
        return f"Initialized: {game_directory}"
    except Exception as e:
        return f"Error initializing: {e}"


@mcp.tool()
def list_files(directory: str) -> str:
    """
    List script files (.txt) in a directory.

    Use this to find file names before calling list_symbols or get_structure.
    Combine with list_directories to navigate the game's script structure.

    Args:
        directory: Relative path to the directory
                  (e.g., "common/national_focus", "events")

    Returns:
        List of .txt file names in the directory.
    """
    return list_files_tool(_ctx, directory)


@mcp.tool()
def list_directories() -> str:
    """
    List all known script directories and their purposes.

    Returns a compact list of directories with descriptions.
    Useful for understanding where different types of scripts are located.

    Returns:
        List of directories with their purposes in Japanese.
    """
    return list_directories_tool()


@mcp.tool()
def find_symbol_at_line(file_path: str, line: int) -> str:
    """
    Find which symbol contains the given line number.

    Use this after search_references returns a file and line number,
    to identify which symbol (event, focus, achievement, etc.) owns that line.
    Returns the symbol name and its line range so you can call get_structure next.

    Args:
        file_path: Relative path to the file
                  (e.g., "events/MUN_Czechoslovakia.txt")
        line: Line number to look up (1-based)

    Returns:
        Symbol name, container type, line range, and a ready-to-use get_structure call.
    """
    return find_symbol_at_line_tool(_ctx, file_path, line)


@mcp.tool()
def list_symbols(file_path: str) -> str:
    """
    List symbols in a specific file.

    Shows symbol names and types without full script content.
    For child elements (e.g., focuses within a focus_tree), use get_structure.

    Args:
        file_path: Relative path to the file
                  (e.g., "common/national_focus/japan.txt")

    Returns:
        Compact list of symbols with their types and key attributes.
    """
    return list_symbols_tool(_ctx, file_path)


@mcp.tool()
def search_references(
    query: str,
    glob_pattern: str = "**/*.txt",
    include_lines: bool = False,
) -> str:
    """
    Search for a string across all game script files.

    Use this to find which files reference a flag, event ID, or any other string.
    By default returns only file paths (token-efficient).
    Set include_lines=True to also return matching line numbers and content.

    Args:
        query: String to search for (literal match)
        glob_pattern: Glob pattern relative to game directory (default: **/*.txt)
        include_lines: If True, include matching line numbers and content

    Returns:
        List of files (and optionally lines) containing the query.
    """
    return search_references_tool(_ctx, query, glob_pattern, include_lines)


@mcp.tool()
def get_structure(file_path: str, symbol: str, key_path: str | None = None) -> str:
    """
    Get the structure of a symbol (keys only, no full content).

    This is the key token-saving tool: shows what keys exist in a block
    without dumping the full script content. Use this to understand
    what a focus, event, or decision contains before requesting specifics.

    Args:
        file_path: Relative path to the file (required)
                  (e.g., "common/national_focus/japan.txt")
        symbol: Name of the symbol to inspect
               (e.g., "JAP_the_unthinkable_option", "japan.1")
        key_path: Optional dot-separated path to navigate into nested blocks
                 (e.g., "completion_reward", "completion_reward.hidden_effect")
                 Paths with 2+ segments trigger full content expansion instead
                 of "[block]" placeholders — use this to read nested conditions.

    Returns:
        Compact structure showing keys and value types.
        Block values show "[block]" instead of full content.
        At depth >= 2 (via key_path), blocks are fully expanded.
    """
    return get_structure_tool(_ctx, file_path, symbol, key_path)


@mcp.tool()
def get_structure_by_id(
    symbol: str,
    glob_pattern: str = "**/*.txt",
    key_path: str | None = None,
) -> str:
    """
    Get the structure of a symbol by its ID, without specifying a file path.

    Use this when you find a reference like `country_event = { id = shroud.4135 }`
    and want to inspect the definition directly — combines text search and parsing
    in one step.

    Args:
        symbol: Symbol ID to find (e.g., "shroud.4135", "end_of_the_cycle")
        glob_pattern: Glob pattern relative to game directory (default: **/*.txt)
                     Use narrower patterns like "events/**/*.txt" for speed.
        key_path: Optional dot-separated path to navigate into nested blocks
                 (e.g., "completion_reward", "completion_reward.hidden_effect")
                 Paths with 2+ segments trigger full content expansion instead
                 of "[block]" placeholders.

    Returns:
        Compact structure showing keys and value types.
        Includes the source file path where the symbol was found.
    """
    return get_structure_by_id_tool(_ctx, symbol, glob_pattern, key_path)


# ASGI app for uvicorn (hot reload support)
app = mcp.streamable_http_app()


def main():
    """Main entry point for the MCP server"""
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
