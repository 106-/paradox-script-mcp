"""
Directory Knowledge Loader

Loads directory knowledge from YAML files based on game type.
"""

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class DirectoryInfo:
    """Information about a script directory"""

    description: str


class DirectoryKnowledge:
    """
    Manages directory knowledge for a specific game.

    Loads from YAML files in the knowledge/{game}/ directory.
    """

    def __init__(self):
        self._directories: dict[str, DirectoryInfo] = {}
        self._game: str | None = None

    @property
    def is_loaded(self) -> bool:
        return self._game is not None

    @property
    def game(self) -> str | None:
        return self._game

    def load(self, game: str) -> None:
        """
        Load directory knowledge for a game.

        Args:
            game: Game identifier (e.g., "hoi4", "eu4")
        """
        knowledge_dir = Path(__file__).parent / game
        yml_path = knowledge_dir / "directories.yml"

        if not yml_path.exists():
            raise FileNotFoundError(f"Knowledge file not found: {yml_path}")

        with open(yml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self._directories = {}
        for path, info in data.get("directories", {}).items():
            self._directories[path] = DirectoryInfo(
                description=info.get("description", ""),
            )

        self._game = game

    def get_info(self, rel_path: str) -> DirectoryInfo | None:
        """
        Get directory information for a given path.

        Matches the most specific directory prefix.
        """
        rel_path = rel_path.replace("\\", "/")

        best_match: str | None = None
        for dir_path in self._directories:
            if rel_path.startswith(dir_path):
                if best_match is None or len(dir_path) > len(best_match):
                    best_match = dir_path

        if best_match:
            return self._directories[best_match]
        return None

    def list_all(self) -> list[tuple[str, str]]:
        """
        List all known directories with descriptions.

        Returns list of (path, description) tuples.
        """
        return [
            (path, info.description) for path, info in sorted(self._directories.items())
        ]


# Global instance
_knowledge = DirectoryKnowledge()


def load_knowledge(game: str) -> None:
    """Load directory knowledge for a game."""
    _knowledge.load(game)


def get_directory_info(rel_path: str) -> DirectoryInfo | None:
    """Get directory information for a given path."""
    return _knowledge.get_info(rel_path)


def list_directories() -> list[tuple[str, str]]:
    """List all known directories with descriptions."""
    return _knowledge.list_all()


def is_knowledge_loaded() -> bool:
    """Check if knowledge is loaded."""
    return _knowledge.is_loaded
