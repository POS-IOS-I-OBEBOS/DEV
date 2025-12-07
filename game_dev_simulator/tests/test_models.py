"""Базовые тесты моделей Game Dev Simulator."""

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game_dev_simulator.core.models import Employee, GameProject, GameStudio, MarketTrend


class ModelsTestCase(unittest.TestCase):
    """Проверяем создание и базовое поведение моделей."""

    def test_create_entities(self) -> None:
        studio = GameStudio(name="Indie Stars", cash=1_000, reputation=5)
        employee = Employee(
            name="Анна",
            role="programmer",
            skill_code=6,
            skill_design=2,
            skill_art=1,
            skill_sound=1,
            salary=50,
        )
        project = GameProject(
            title="RPG Dream",
            genre="RPG",
            platform="PC",
            complexity=20,
        )

        studio.employees.append(employee)
        studio.projects.append(project)

        self.assertEqual(studio.name, "Indie Stars")
        self.assertEqual(studio.employees[0].name, "Анна")
        self.assertEqual(studio.projects[0].title, "RPG Dream")

    def test_employee_work_and_rest(self) -> None:
        employee = Employee(
            name="Борис",
            role="designer",
            skill_code=3,
            skill_design=5,
            skill_art=2,
            skill_sound=1,
            salary=40,
        )

        contributions = employee.work_on_task()
        self.assertGreater(contributions["design"], 0)
        self.assertEqual(employee.fatigue, 10)

        employee.rest(hours=6)
        self.assertEqual(employee.fatigue, 4)

    def test_project_advances_progress(self) -> None:
        employee = Employee(
            name="Вика",
            role="programmer",
            skill_code=10,
            skill_design=1,
            skill_art=1,
            skill_sound=1,
            salary=30,
        )
        project = GameProject(
            title="Space Saga",
            genre="Strategy",
            platform="PC",
            complexity=10,
            assigned_employees=[employee],
        )
        trend = MarketTrend(trending_genres=["Strategy"], popular_platforms=["PC"])

        initial_progress = project.progress
        project.advance_week(trend=trend)

        self.assertGreater(project.progress, initial_progress)
        self.assertGreater(project.quality_code, 0)


if __name__ == "__main__":
    unittest.main()
