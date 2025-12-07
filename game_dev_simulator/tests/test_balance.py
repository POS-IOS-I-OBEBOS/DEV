"""Тесты для функций расчёта оценки игры, отзывов и продаж."""

import random
import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game_dev_simulator.core.balance import (
    calculate_game_score,
    calculate_sales,
    generate_reviews,
)
from game_dev_simulator.core.events import handle_release_event
from game_dev_simulator.core.models import GameProject, GameStudio, MarketTrend


class BalanceFunctionsTestCase(unittest.TestCase):
    """Проверяем вспомогательные функции финансового модуля."""

    def setUp(self) -> None:
        random.seed(42)
        self.project = GameProject(
            title="Test Game",
            genre="RPG",
            platform="PC",
            complexity=20,
            quality_code=60,
            quality_design=55,
            quality_art=50,
            quality_sound=45,
        )
        self.studio = GameStudio(name="Test", cash=1000, reputation=3)
        self.trend = MarketTrend(trending_genres=["RPG"], popular_platforms=["PC"])

    def test_calculate_game_score_in_range(self) -> None:
        score = calculate_game_score(self.project, self.trend, self.studio)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_generate_reviews_count(self) -> None:
        score = 65
        reviews = generate_reviews(score)
        self.assertGreaterEqual(len(reviews), 3)
        self.assertLessEqual(len(reviews), 7)

    def test_handle_release_event_structure(self) -> None:
        result = handle_release_event(self.project, self.studio, self.trend)
        self.assertIn("score", result)
        self.assertIn("reviews", result)
        self.assertIn("income", result)
        self.assertIsInstance(result["reviews"], list)
        self.assertGreater(result["income"], 0)


if __name__ == "__main__":
    unittest.main()
