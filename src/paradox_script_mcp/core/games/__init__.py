"""
Game plugin abstraction layer.

Each game implements GamePlugin to provide game-specific symbol search logic.
Register new games in REGISTRY.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


class GamePlugin(ABC):
    """
    Abstract base class for game-specific logic.

    Subclass this for each supported game and register in REGISTRY.
    """

    @abstractmethod
    def find_symbol_block(self, data: Any, symbol: str) -> Any | None:
        """
        Find a symbol block in parsed file data.

        Args:
            data: Parsed file data (ScriptData or dict)
            symbol: Symbol name / ID to find

        Returns:
            The block if found, None otherwise.
        """
        ...


def _get_registry() -> dict[str, type[GamePlugin]]:
    from paradox_script_mcp.core.games.hoi4 import Hoi4Plugin
    from paradox_script_mcp.core.games.generic import GenericPlugin

    return {
        "hoi4": Hoi4Plugin,
        "_generic": GenericPlugin,
    }


def get_plugin(game_type: str) -> GamePlugin:
    """
    Return an instantiated plugin for the given game type.

    Falls back to GenericPlugin for unknown games.
    """
    registry = _get_registry()
    cls = registry.get(game_type) or registry["_generic"]
    return cls()
