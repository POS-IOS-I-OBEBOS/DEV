"""Основной цикл симуляции разработки игр по неделям."""

from __future__ import annotations

import random
from typing import Dict, List

from .balance import (
    BalanceConfig,
    calculate_game_score,
    calculate_sales,
    generate_reviews,
    get_default_balance_config,
)
from .events import GameEvent
from .models import Employee, GameProject, GameStudio, MarketTrend


class GameSimulation:
    """Управляет развитием студии, проектами и событиями по неделям."""

    def __init__(
        self,
        studio: GameStudio,
        market_trend: MarketTrend | None = None,
        balance_config: BalanceConfig | None = None,
    ) -> None:
        self.studio = studio
        self.current_week = 1
        self.current_year = 1
        self.market_trend = market_trend or MarketTrend()
        self.balance_config = balance_config or get_default_balance_config()

    def run_step(self) -> None:
        """Выполнить один игровой ход (неделю)."""

        self._pay_salaries()
        self._advance_projects()
        self._apply_market_trends()
        self._process_random_events()
        self._check_releases()
        self._advance_calendar()

    def release_game(self, project: GameProject) -> None:
        """Релиз проекта: расчёт продаж, рост репутации и перенос в архив."""

        base_price = 30
        market_size = 50_000

        score = calculate_game_score(
            project, market_trend=self.market_trend, studio=self.studio, config=self.balance_config
        )
        revenue = calculate_sales(
            score, base_price=base_price, market_size=market_size, config=self.balance_config
        )
        reviews = generate_reviews(score)
        reputation_gain = max(1, int(score // 20))

        self.studio.cash += revenue
        self.studio.reputation += reputation_gain
        project.status = "released"
        if project in self.studio.projects:
            self.studio.projects.remove(project)
        self.studio.finished_projects.append(project)
        return {"score": score, "reviews": reviews, "income": revenue}

    def get_state_summary(self) -> Dict[str, object]:
        """Вернёт краткую сводку состояния студии и проектов."""

        return {
            "week": self.current_week,
            "year": self.current_year,
            "cash": self.studio.cash,
            "reputation": self.studio.reputation,
            "active_projects": [p.title for p in self.studio.projects],
            "finished_projects": [p.title for p in self.studio.finished_projects],
            "employees": [e.name for e in self.studio.employees],
        }

    def to_dict(self) -> Dict[str, object]:
        """Сериализует текущее состояние симуляции в словарь."""

        employees_data = [self._employee_to_dict(emp) for emp in self.studio.employees]
        projects_data = [self._project_to_dict(project, employees_data) for project in self.studio.projects]
        finished_data = [self._project_to_dict(project, employees_data) for project in self.studio.finished_projects]

        return {
            "current_week": self.current_week,
            "current_year": self.current_year,
            "balance_config": self.balance_config.as_dict(),
            "market_trend": {
                "trending_genres": list(self.market_trend.trending_genres),
                "popular_platforms": list(self.market_trend.popular_platforms),
            },
            "studio": {
                "name": self.studio.name,
                "cash": self.studio.cash,
                "reputation": self.studio.reputation,
                "employees": employees_data,
                "projects": projects_data,
                "finished_projects": finished_data,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "GameSimulation":
        """Восстанавливает симуляцию из сериализованной структуры."""

        studio_data = data.get("studio", {})
        employees = [cls._employee_from_dict(emp_data) for emp_data in studio_data.get("employees", [])]
        studio = GameStudio(
            name=str(studio_data.get("name", "Unnamed Studio")),
            cash=int(studio_data.get("cash", 0)),
            reputation=int(studio_data.get("reputation", 0)),
            employees=employees,
        )

        for project_data in studio_data.get("projects", []):
            project = cls._project_from_dict(project_data, employees)
            studio.projects.append(project)

        for project_data in studio_data.get("finished_projects", []):
            project = cls._project_from_dict(project_data, employees)
            studio.finished_projects.append(project)

        trend_data = data.get("market_trend", {})
        market_trend = MarketTrend(
            trending_genres=list(trend_data.get("trending_genres", [])),
            popular_platforms=list(trend_data.get("popular_platforms", [])),
        )

        balance_config_data = data.get("balance_config")
        balance_config = (
            BalanceConfig(**balance_config_data) if isinstance(balance_config_data, dict) else None
        )

        simulation = cls(studio=studio, market_trend=market_trend, balance_config=balance_config)
        simulation.current_week = int(data.get("current_week", 1))
        simulation.current_year = int(data.get("current_year", 1))
        return simulation

    def _pay_salaries(self) -> None:
        role_base_salary = {
            "programmer": self.balance_config.base_salary_programmer,
            "designer": self.balance_config.base_salary_designer,
            "artist": self.balance_config.base_salary_artist,
            "sound": self.balance_config.base_salary_sound,
            "producer": self.balance_config.base_salary_producer,
        }

        total_salary = 0
        for employee in self.studio.employees:
            fallback = role_base_salary.get(employee.role, self.balance_config.base_salary_programmer)
            total_salary += employee.salary or fallback
        self.studio.cash -= total_salary

    def _advance_projects(self) -> None:
        for project in list(self.studio.projects):
            if project.status == "in_dev":
                project.advance_week(trend=self.market_trend, fatigue_increase=self.balance_config.fatigue_per_week)

        self._recover_idle_employees()

    def _recover_idle_employees(self) -> None:
        """Часть усталости снимается у сотрудников, не работающих над проектом."""

        assigned = [
            employee for project in self.studio.projects for employee in project.assigned_employees
        ]
        for employee in self.studio.employees:
            if employee not in assigned:
                employee.rest(hours=self.balance_config.rest_recovery_per_week)

    def _apply_market_trends(self) -> None:
        for project in self.studio.projects:
            if project.status != "in_dev":
                continue
            bonus = (
                self.balance_config.trend_genre_bonus
                if project.genre in self.market_trend.trending_genres
                else 0.0
            )
            project.progress = min(100.0, project.progress + bonus * 2)

    def _process_random_events(self) -> None:
        roll = random.random()
        if roll > self.balance_config.event_chance_per_week:
            return

        event_roll = random.random()
        if event_roll < 0.4 and self.studio.employees:
            sick_employee = random.choice(self.studio.employees)
            sick_employee.fatigue = min(100, sick_employee.fatigue + 20)
            event = GameEvent(name="Болезнь сотрудника", effect=-(sick_employee.salary or 10))
            self._apply_event_effect(event)
        elif event_roll < 0.7:
            payment = 200
            event = GameEvent(name="Контрактная работа", effect=payment)
            self._apply_event_effect(event)
        else:
            event = GameEvent(name="Кризис рынка", effect=-150)
            self._apply_event_effect(event)

    def _check_releases(self) -> None:
        for project in list(self.studio.projects):
            if project.status == "in_dev" and project.progress >= 100:
                self.release_game(project)

    def _advance_calendar(self) -> None:
        self.current_week += 1
        if self.current_week > 52:
            self.current_week = 1
            self.current_year += 1

    def _apply_event_effect(self, event: GameEvent) -> None:
        self.studio.cash += event.effect

    @staticmethod
    def _employee_to_dict(employee: "Employee") -> Dict[str, object]:
        return {
            "name": employee.name,
            "role": employee.role,
            "skill_code": employee.skill_code,
            "skill_design": employee.skill_design,
            "skill_art": employee.skill_art,
            "skill_sound": employee.skill_sound,
            "salary": employee.salary,
            "fatigue": employee.fatigue,
        }

    @staticmethod
    def _employee_from_dict(data: Dict[str, object]) -> "Employee":
        return Employee(
            name=str(data.get("name", "")),
            role=str(data.get("role", "programmer")),
            skill_code=int(data.get("skill_code", 0)),
            skill_design=int(data.get("skill_design", 0)),
            skill_art=int(data.get("skill_art", 0)),
            skill_sound=int(data.get("skill_sound", 0)),
            salary=int(data.get("salary", 0)),
            fatigue=int(data.get("fatigue", 0)),
        )

    @staticmethod
    def _project_to_dict(project: GameProject, employees_data: List[Dict[str, object]]) -> Dict[str, object]:
        assigned_indices: List[int] = []
        for employee in project.assigned_employees:
            try:
                idx = next(
                    i
                    for i, data in enumerate(employees_data)
                    if data.get("name") == employee.name and data.get("role") == employee.role
                )
            except StopIteration:
                continue
            assigned_indices.append(idx)

        return {
            "title": project.title,
            "genre": project.genre,
            "platform": project.platform,
            "complexity": project.complexity,
            "progress": project.progress,
            "quality_code": project.quality_code,
            "quality_design": project.quality_design,
            "quality_art": project.quality_art,
            "quality_sound": project.quality_sound,
            "status": project.status,
            "assigned_employees": assigned_indices,
        }

    @staticmethod
    def _project_from_dict(data: Dict[str, object], employees: List["Employee"]) -> GameProject:
        project = GameProject(
            title=str(data.get("title", "Unnamed Project")),
            genre=str(data.get("genre", "")),
            platform=str(data.get("platform", "")),
            complexity=int(data.get("complexity", 0)),
            progress=float(data.get("progress", 0.0)),
            quality_code=float(data.get("quality_code", 0.0)),
            quality_design=float(data.get("quality_design", 0.0)),
            quality_art=float(data.get("quality_art", 0.0)),
            quality_sound=float(data.get("quality_sound", 0.0)),
            status=str(data.get("status", "in_dev")),
        )

        for idx in data.get("assigned_employees", []):
            if isinstance(idx, int) and 0 <= idx < len(employees):
                project.assigned_employees.append(employees[idx])
        return project

