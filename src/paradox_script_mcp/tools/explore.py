"""
Directory exploration tool
"""

from paradox_script_mcp.knowledge.directory_map import (
    list_directories,
    is_knowledge_loaded,
)


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
