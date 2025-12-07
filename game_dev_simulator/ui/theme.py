"""Тема оформления для pygame-интерфейса Game Dev Simulator."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Tuple

import pygame

Color = Tuple[int, int, int]


@dataclass
class Theme:
    """Набор цветов и констант для UI.

    Все размеры и отступы сосредоточены в одном месте, чтобы облегчить
    настройку визуального стиля.
    """

    # Геометрия окна
    WINDOW_WIDTH: int = 1280
    WINDOW_HEIGHT: int = 720
    STATUS_HEIGHT: int = 64
    LOG_HEIGHT: int = 140
    PANEL_PADDING: int = 12
    CARD_PADDING: int = 10
    SCROLL_STEP: int = 40
    BUTTON_HEIGHT: int = 44
    BUTTON_SPACING: int = 10

    # Шрифты
    FONT_NAME: str = "arial"
    FONT_SIZE: int = 18
    FONT_SIZE_TITLE: int = 22

    # Цвета основы
    BG: Color = (23, 26, 33)
    PANEL: Color = (32, 36, 45)
    PANEL_DARK: Color = (28, 31, 40)
    STATUS_BG: Color = (36, 44, 58)
    LOG_BG: Color = (26, 29, 37)

    # Текст и акценты
    TEXT: Color = (235, 240, 246)
    SUBTEXT: Color = (190, 196, 210)
    ACCENT: Color = (110, 188, 255)
    ACCENT_SOFT: Color = (86, 140, 198)
    SUCCESS: Color = (76, 175, 80)
    WARNING: Color = (255, 193, 7)
    ERROR: Color = (244, 67, 54)

    # Кнопки
    BUTTON_BG: Color = (56, 68, 90)
    BUTTON_BG_HOVER: Color = (70, 88, 115)
    BUTTON_BG_ACTIVE: Color = (90, 120, 150)

    # Прогресс-бары
    PROGRESS_ACTIVE: Color = (110, 188, 255)
    PROGRESS_RELEASED: Color = (88, 215, 141)
    PROGRESS_CANCELLED: Color = (190, 90, 90)
    PROGRESS_BG: Color = (45, 50, 60)

    # Прозрачность/эффекты
    OVERLAY_ALPHA: int = 170
    HOVER_BORDER: Color = (255, 255, 255)

    # Цвета для ролей сотрудников
    role_colors: dict[str, Color] = field(
        default_factory=lambda: {
            "programmer": (86, 156, 214),  # синий
            "designer": (92, 184, 115),  # зеленый
            "artist": (199, 134, 203),  # розово-фиолетовый
            "sound": (243, 156, 92),  # оранжевый
            "producer": (193, 165, 79),  # золотистый
        }
    )

    # Загруженные иконки сотрудников по ролям
    employee_icons: Dict[str, pygame.Surface] = field(default_factory=dict, compare=False)

    def as_dict(self) -> dict:
        """Отладочное представление темы в виде словаря."""

        return self.__dict__.copy()


DEFAULT_THEME = Theme()


def load_employee_icons(path: str | os.PathLike[str]) -> Dict[str, pygame.Surface]:
    """Загружает иконки сотрудников по ролям из указанной папки.

    Если файл не найден, просто пропускаем его, чтобы UI мог
    использовать примитивные спрайты вместо иконок.
    """

    icons: Dict[str, pygame.Surface] = {}
    base_path = Path(path)
    for role in ["programmer", "designer", "artist", "sound", "producer"]:
        file_path = base_path / f"{role}.png"
        try:
            image = pygame.image.load(file_path).convert_alpha()
        except FileNotFoundError:
            # Нет иконки для роли — не считаем это ошибкой
            continue
        except Exception as exc:  # pragma: no cover - диагностическое предупреждение
            print(f"[icons] Не удалось загрузить {file_path}: {exc}")
            continue
        icons[role] = image
    return icons


__all__ = ["Theme", "DEFAULT_THEME", "Color", "load_employee_icons"]
