"""
Game context management for Paradox Script MCP

Simple path management - no caching, no indexing.
Files are parsed on demand using paradox-script-parser.
"""

from pathlib import Path

from paradox_script_mcp.knowledge.directory_map import load_knowledge


class GameContext:
    """
    Manages game directory path and knowledge.

    No caching or indexing - just path management.
    Files are parsed on demand when tools need them.
    """

    def __init__(self):
        self._game_directory: Path | None = None
        self._game_type: str | None = None

    def initialize(self, game_directory: str, game_type: str = "hoi4") -> None:
        """
        Set the game directory path and load knowledge.

        Args:
            game_directory: Path to the game directory
            game_type: Game type identifier (default: "hoi4")
        """
        path = Path(game_directory)
        if not path.exists():
            raise ValueError(f"Game directory not found: {game_directory}")
        if not path.is_dir():
            raise ValueError(f"Not a directory: {game_directory}")

        self._game_directory = path
        self._game_type = game_type

        # Load knowledge for this game type
        load_knowledge(game_type)

    @property
    def game_directory(self) -> Path | None:
        """Get the game directory path"""
        return self._game_directory

    @property
    def game_type(self) -> str | None:
        """Get the game type"""
        return self._game_type

    @property
    def is_initialized(self) -> bool:
        """Check if game directory is set"""
        return self._game_directory is not None

    def resolve_path(self, rel_path: str) -> Path | None:
        """
        Resolve a relative path to an absolute path.

        Args:
            rel_path: Relative path within game directory

        Returns:
            Absolute path if file exists, None otherwise.
        """
        if not self._game_directory:
            return None

        # Normalize path separators
        rel_path = rel_path.replace("\\", "/")

        full_path = self._game_directory / rel_path
        if full_path.exists():
            return full_path
        return None
