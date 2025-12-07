"""Утилиты для сохранения и загрузки состояния игры."""

from __future__ import annotations

import json
import os
from typing import Any, Dict

from game_dev_simulator.core import GameSimulation


class Storage:
    """Простое хранилище в памяти (оставлено для совместимости CLI)."""

    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}

    def save(self, key: str, value: Any) -> None:
        """Сохранить состояние в память."""
        self._data[key] = value

    def load(self, key: str, default: Any | None = None) -> Any:
        """Загрузить состояние из памяти."""
        return self._data.get(key, default)


def save_game(simulation: GameSimulation, filename: str = "save/game_save.json") -> None:
    """Сериализует состояние симуляции и сохраняет в JSON-файл."""

    data = simulation.to_dict()
    directory = os.path.dirname(filename)
    if directory:
        os.makedirs(directory, exist_ok=True)

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def load_game(filename: str = "save/game_save.json") -> GameSimulation:
    """Загружает сохранённую игру из JSON и восстанавливает симуляцию."""

    if not os.path.exists(filename):
        raise FileNotFoundError(f"Сохранение {filename} не найдено")

    with open(filename, "r", encoding="utf-8") as file:
        data = json.load(file)

    return GameSimulation.from_dict(data)
