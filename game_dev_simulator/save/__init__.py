"""Модуль для сохранения и загрузки прогресса."""

from .storage import Storage, load_game, save_game

__all__ = ["Storage", "save_game", "load_game"]
