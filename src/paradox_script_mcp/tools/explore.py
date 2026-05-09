"""
Directory exploration tool
"""

from paradox_script_mcp.core.game import GameContext
from paradox_script_mcp.knowledge.directory_map import (
    is_knowledge_loaded,
    list_directories,
)


def list_files_tool(ctx: GameContext, directory: str) -> str:
    """
    List script files in a directory.

    Args:
        ctx: The game context
        directory: Relative path to the directory (e.g., "common/national_focus")

    Returns:
        List of .txt file names in the directory.
    """
    if not ctx.is_initialized or ctx.game_directory is None:
        return "Error: Game not initialized. Call init_game first."

    target = ctx.game_directory / directory
    if not target.exists():
        return f"Error: Directory not found: {directory}"
    if not target.is_dir():
        return f"Error: Not a directory: {directory}"

    files = sorted(
        f.name for f in target.iterdir() if f.is_file() and f.suffix == ".txt"
    )
    if not files:
        return f"No .txt files found in {directory}"

    return "\n".join(files)


def list_directories_tool() -> str:
    """
    List all known directories and their purposes

    Returns a compact list for token efficiency.
    """
    if not is_knowledge_loaded():
        return "Error: Knowledge not loaded. Call init_game first."

    lines = []
    for path, description in list_directories():
        lines.append(f"{path}/ -> {description}")
    return "\n".join(lines)
