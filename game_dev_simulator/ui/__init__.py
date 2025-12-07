"""Интерфейсы пользователя симулятора."""

from .cli import GameCLI, run_cli
from .pygame_ui import GamePygameUI
from .theme import DEFAULT_THEME, Theme

__all__ = ["GameCLI", "GamePygameUI", "run_cli", "DEFAULT_THEME", "Theme"]
