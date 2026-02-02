"""
Paradox Script MCP Server

Main entry point for the MCP server.
Provides tools for efficient discovery of HOI4 game scripts.
"""

from mcp.server.fastmcp import FastMCP

from paradox_script_mcp.core.game import GameContext
from paradox_script_mcp.tools.explore import list_directories_tool
from paradox_script_mcp.tools.symbols import list_symbols_tool
from paradox_script_mcp.tools.structure import get_structure_tool

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

    Returns:
        Compact structure showing keys and value types.
        Block values show "[block]" instead of full content.
    """
    return get_structure_tool(_ctx, file_path, symbol, key_path)


# ASGI app for uvicorn (hot reload support)
app = mcp.streamable_http_app()


def main():
    """Main entry point for the MCP server"""
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()
