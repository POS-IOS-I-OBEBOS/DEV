"""Модели для симуляции разработки игр и рынка."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence


@dataclass
class Employee:
    """Сотрудник игровой студии с базовыми показателями навыков."""

    name: str
    role: str  # programmer, designer, artist, sound, producer
    skill_code: int
    skill_design: int
    skill_art: int
    skill_sound: int
    salary: int
    fatigue: int = 0

    def work_on_task(self, fatigue_increase: int = 10) -> Dict[str, float]:
        """Выполняет задачу и возвращает вклад по направлениям.

        Усталость снижает эффективность (не ниже 50%), затем усталость растёт. Параметр
        ``fatigue_increase`` позволяет управлять ростом усталости снаружи (через конфиг).
        """

        fatigue_factor = max(0.5, 1.0 - self.fatigue / 100)
        contributions = {
            "code": self.skill_code * fatigue_factor,
            "design": self.skill_design * fatigue_factor,
            "art": self.skill_art * fatigue_factor,
            "sound": self.skill_sound * fatigue_factor,
        }
        self.fatigue = min(100, self.fatigue + fatigue_increase)
        return contributions

    def rest(self, hours: int = 8) -> None:
        """Сбрасывает усталость, имитируя отдых."""

        self.fatigue = max(0, self.fatigue - hours)

    def level_up(self) -> None:
        """Повышает навыки в зависимости от роли сотрудника."""

        role_focus = {
            "programmer": "skill_code",
            "designer": "skill_design",
            "artist": "skill_art",
            "sound": "skill_sound",
            "producer": None,
        }
        focus_attr = role_focus.get(self.role)
        if focus_attr:
            setattr(self, focus_attr, getattr(self, focus_attr) + 1)
        else:
            # Продюсер слегка растит все навыки для универсальности
            self.skill_code += 1
            self.skill_design += 1
            self.skill_art += 1
            self.skill_sound += 1


@dataclass
class MarketTrend:
    """Отслеживает тренды по жанрам и платформам."""

    trending_genres: List[str] = field(default_factory=list)
    popular_platforms: List[str] = field(default_factory=list)

    def update_trends(self, new_genres: Sequence[str] | None = None, new_platforms: Sequence[str] | None = None) -> None:
        """Обновляет списки трендов (детерминированно без случайности)."""

        if new_genres is not None:
            self.trending_genres = list(new_genres)
        else:
            self.trending_genres = self.trending_genres[::-1]

        if new_platforms is not None:
            self.popular_platforms = list(new_platforms)
        else:
            self.popular_platforms = self.popular_platforms[::-1]

    def get_genre_multiplier(self, genre: str) -> float:
        """Возвращает мультипликатор интереса рынка к жанру."""

        return 1.2 if genre in self.trending_genres else 1.0


@dataclass
class GameProject:
    """Игровой проект со своими метриками прогресса и качества."""

    title: str
    genre: str
    platform: str
    complexity: int
    progress: float = 0.0
    quality_code: float = 0.0
    quality_design: float = 0.0
    quality_art: float = 0.0
    quality_sound: float = 0.0
    status: str = "in_dev"  # in_dev, released, cancelled
    assigned_employees: List[Employee] = field(default_factory=list)

    def apply_employee_work(
        self, employee: Employee, trend: MarketTrend | None = None, fatigue_increase: int = 10
    ) -> None:
        """Применяет вклад сотрудника в прогресс и качество проекта."""

        contributions = employee.work_on_task(fatigue_increase=fatigue_increase)
        productivity = {
            "programmer": contributions["code"],
            "designer": contributions["design"],
            "artist": contributions["art"],
            "sound": contributions["sound"],
            "producer": sum(contributions.values()) * 0.5,
        }
        primary = productivity.get(employee.role, sum(contributions.values()) * 0.25)

        trend_multiplier = trend.get_genre_multiplier(self.genre) if trend else 1.0
        progress_gain = (primary / max(1, self.complexity)) * 10 * trend_multiplier
        self.progress = min(100.0, self.progress + progress_gain)

        self.quality_code += contributions["code"] * 0.1
        self.quality_design += contributions["design"] * 0.1
        self.quality_art += contributions["art"] * 0.1
        self.quality_sound += contributions["sound"] * 0.1

    def advance_week(self, trend: MarketTrend | None = None, fatigue_increase: int = 10) -> None:
        """Продвигает проект на неделю, обрабатывая вклад назначенных сотрудников."""

        if self.status != "in_dev":
            return

        for employee in self.assigned_employees:
            self.apply_employee_work(employee, trend=trend, fatigue_increase=fatigue_increase)


@dataclass
class GameStudio:
    """Студия с сотрудниками, активными и завершёнными проектами."""

    name: str
    cash: int
    reputation: int
    employees: List[Employee] = field(default_factory=list)
    projects: List[GameProject] = field(default_factory=list)
    finished_projects: List[GameProject] = field(default_factory=list)

    def finish_project(self, project: GameProject) -> None:
        """Переносит проект из активных в завершённые и поднимает репутацию."""

        if project in self.projects:
            self.projects.remove(project)
            self.finished_projects.append(project)
            self.reputation += 1
