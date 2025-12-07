"""События, влияющие на симуляцию."""

from __future__ import annotations

from dataclasses import dataclass

from .balance import BalanceConfig, calculate_game_score, calculate_sales, generate_reviews
from .models import GameProject, GameStudio, MarketTrend


@dataclass
class GameEvent:
    """Простая структура события."""

    name: str
    effect: int = 0

    def describe(self) -> str:
        """Описание события для логов."""
        return f"Событие: {self.name}, эффект: {self.effect}"


def handle_release_event(
    project: GameProject,
    studio: GameStudio,
    market_trend: MarketTrend,
    balance_config: BalanceConfig | None = None,
) -> dict:
    """Готовит данные по релизу: оценка, отзывы и продажи."""

    base_price = 30
    market_size = 50_000

    score = calculate_game_score(project, market_trend, studio, config=balance_config)
    reviews = generate_reviews(score)
    sales_income = calculate_sales(
        score, base_price=base_price, market_size=market_size, config=balance_config
    )

    return {
        "score": score,
        "reviews": reviews,
        "sales": sales_income // base_price,
        "income": sales_income,
    }


def demo() -> None:
    """Пример использования расчёта релиза с выводом в консоль."""

    studio = GameStudio(name="Demo Studio", cash=1_000, reputation=5)
    project = GameProject(
        title="Space Colony",
        genre="Strategy",
        platform="PC",
        complexity=20,
        quality_code=70,
        quality_design=65,
        quality_art=60,
        quality_sound=55,
    )
    trend = MarketTrend(trending_genres=["Strategy", "RPG"], popular_platforms=["PC", "Console"])

    result = handle_release_event(project, studio, trend)

    print("=== Демо расчёта релиза ===")
    print(f"Игра: {project.title}")
    print(f"Итоговый балл: {result['score']:.1f}")
    print(f"Прогноз продаж: {result['sales']} копий")
    print(f"Доход: ${result['income']}")
    print("Отзывы:")
    for review in result["reviews"]:
        print(f"- {review}")


if __name__ == "__main__":
    demo()
