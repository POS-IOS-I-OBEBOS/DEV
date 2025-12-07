"""Тесты для игрового цикла симуляции."""

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game_dev_simulator.core import GameSimulation
from game_dev_simulator.core.balance import BalanceConfig
from game_dev_simulator.core.models import Employee, GameProject, GameStudio, MarketTrend


class SimulationTestCase(unittest.TestCase):
    """Проверяем, что недельный шаг симуляции корректно изменяет состояние."""

    def test_run_step_pays_salaries_and_releases_project(self) -> None:
        employee = Employee(
            name="Анна",
            role="programmer",
            skill_code=8,
            skill_design=2,
            skill_art=1,
            skill_sound=1,
            salary=50,
        )
        project = GameProject(
            title="Arcade",
            genre="Arcade",
            platform="PC",
            complexity=1,
            progress=100,
            assigned_employees=[employee],
        )
        studio = GameStudio(
            name="Test Studio",
            cash=200,
            reputation=0,
            employees=[employee],
            projects=[project],
        )
        # Обнуляем влияние событий и доходов, чтобы проверить зарплаты и релиз
        balance_config = BalanceConfig(
            base_salary_programmer=50,
            base_project_income_multiplier=0.0,
            event_chance_per_week=0.0,
            random_score_deviation=0.0,
            fatigue_per_week=10,
            rest_recovery_per_week=5,
            base_salary_designer=0,
            base_salary_artist=0,
            base_salary_sound=0,
            base_salary_producer=0,
            trend_genre_bonus=0.0,
            trend_platform_bonus=0.0,
        )
        trend = MarketTrend(trending_genres=["Arcade"], popular_platforms=["PC"])
        simulation = GameSimulation(studio, market_trend=trend, balance_config=balance_config)

        simulation.run_step()

        self.assertEqual(simulation.current_week, 2)
        self.assertEqual(studio.cash, 150)  # 200 - salary 50, без доп.дохода
        self.assertEqual(len(studio.projects), 0)
        self.assertEqual(len(studio.finished_projects), 1)
        self.assertEqual(studio.finished_projects[0].status, "released")


if __name__ == "__main__":
    unittest.main()
