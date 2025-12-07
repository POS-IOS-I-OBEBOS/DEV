"""Интерфейсы пользователя симулятора."""

from .cli import GameCLI, run_cli
from .pygame_ui import GamePygameUI

__all__ = ["GameCLI", "GamePygameUI", "run_cli"]
