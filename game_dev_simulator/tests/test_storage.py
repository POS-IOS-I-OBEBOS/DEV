"""Тесты сериализации и восстановления состояния симуляции."""

import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game_dev_simulator.core import BalanceConfig, GameSimulation
from game_dev_simulator.core.models import Employee, GameProject, GameStudio, MarketTrend
from game_dev_simulator.save import load_game, save_game


class StorageTestCase(unittest.TestCase):
    """Проверяем сохранение, загрузку и преобразование в словарь."""

    def _build_simulation(self, balance_config: BalanceConfig | None = None) -> GameSimulation:
        employees = [
            Employee(
                name="Анна",
                role="programmer",
                skill_code=6,
                skill_design=3,
                skill_art=1,
                skill_sound=1,
                salary=30,
            ),
            Employee(
                name="Борис",
                role="designer",
                skill_code=2,
                skill_design=5,
                skill_art=2,
                skill_sound=2,
                salary=25,
            ),
        ]
        project = GameProject(
            title="Adventure Quest",
            genre="Adventure",
            platform="PC",
            complexity=20,
            progress=40,
        )
        project.assigned_employees.extend(employees)
        studio = GameStudio(
            name="Save Test Studio",
            cash=800,
            reputation=3,
            employees=employees,
            projects=[project],
        )
        trend = MarketTrend(trending_genres=["Adventure"], popular_platforms=["PC", "Console"])
        return GameSimulation(studio=studio, market_trend=trend, balance_config=balance_config)

    def test_to_dict_and_from_dict_roundtrip(self) -> None:
        custom_config = BalanceConfig(event_chance_per_week=0.1, rest_recovery_per_week=8)
        simulation = self._build_simulation(balance_config=custom_config)
        data = simulation.to_dict()

        restored = GameSimulation.from_dict(data)

        self.assertEqual(restored.studio.name, simulation.studio.name)
        self.assertEqual(len(restored.studio.employees), 2)
        self.assertEqual(restored.studio.projects[0].title, "Adventure Quest")
        self.assertEqual(restored.studio.projects[0].assigned_employees[0].name, "Анна")
        self.assertEqual(restored.market_trend.trending_genres, ["Adventure"])
        self.assertAlmostEqual(restored.balance_config.event_chance_per_week, 0.1)

    def test_save_and_load_game_file(self) -> None:
        simulation = self._build_simulation()
        with TemporaryDirectory() as temp_dir:
            filepath = os.path.join(temp_dir, "game.json")
            save_game(simulation, filename=filepath)

            loaded = load_game(filename=filepath)

            self.assertEqual(loaded.studio.cash, simulation.studio.cash)
            self.assertEqual(loaded.current_week, simulation.current_week)
            self.assertEqual(len(loaded.studio.projects), 1)


if __name__ == "__main__":
    unittest.main()
