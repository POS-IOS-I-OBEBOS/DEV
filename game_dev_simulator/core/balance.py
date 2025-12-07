"""Учет бюджета студии разработки игр и расчёты релизов."""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass
from typing import List, TYPE_CHECKING

from .models import GameProject, GameStudio, MarketTrend

if TYPE_CHECKING:
    from .events import GameEvent


@dataclass
class BalanceConfig:
    """Единая точка конфигурации финансов и баланса симуляции."""

    base_salary_programmer: int = 25
    base_salary_designer: int = 22
    base_salary_artist: int = 20
    base_salary_sound: int = 20
    base_salary_producer: int = 30
    base_project_income_multiplier: float = 1.0
    trend_genre_bonus: float = 0.2
    trend_platform_bonus: float = 0.1
    random_score_deviation: float = 5.0
    fatigue_per_week: int = 10
    rest_recovery_per_week: int = 5
    event_chance_per_week: float = 0.25

    def as_dict(self) -> dict:
        """Преобразует конфиг в словарь (удобно для отладки или логов)."""

        return asdict(self)


def get_default_balance_config() -> BalanceConfig:
    """Возвращает конфигурацию баланса по умолчанию."""

    return BalanceConfig()


class BalanceManager:
    """Простая заглушка для управления финансами."""

    def __init__(self, starting_money: int = 0) -> None:
        self.money = starting_money

    def pay_salaries(self, total_salary: int) -> None:
        """Выплата зарплат команде."""

        self.money -= total_salary

    def invest_in_marketing(self, amount: int) -> None:
        """Вложения в маркетинг увеличивают потенциальный доход."""

        self.money -= amount

    def apply_event(self, event: GameEvent) -> None:
        """Применить финансовый эффект от события (заглушка)."""

        self.money += event.effect


def calculate_game_score(
    project: GameProject,
    market_trend: MarketTrend,
    studio: GameStudio,
    config: BalanceConfig | None = None,
) -> float:
    """Вычисляет итоговый «оценочный балл» игры.

    Учитывается качество по всем направлениям, тренды жанров/платформ и
    репутация студии. Добавляется небольшой случайный разброс, чтобы избежать
    детерминированности.
    """

    config = config or get_default_balance_config()

    quality_components = [
        project.quality_code,
        project.quality_design,
        project.quality_art,
        project.quality_sound,
    ]
    avg_quality = sum(quality_components) / max(1, len(quality_components))

    genre_multiplier = (
        1 + config.trend_genre_bonus if project.genre in market_trend.trending_genres else 1.0
    )
    platform_multiplier = (
        1 + config.trend_platform_bonus
        if project.platform in market_trend.popular_platforms
        else 1.0
    )
    reputation_factor = 1 + studio.reputation * 0.02

    random_jitter = random.uniform(-config.random_score_deviation, config.random_score_deviation)
    score = avg_quality * genre_multiplier * platform_multiplier * reputation_factor
    score = max(0.0, min(100.0, score + random_jitter))
    return score


def generate_reviews(score: float) -> List[str]:
    """Генерирует набор коротких отзывов в стиле игровых СМИ."""

    negative_pool = [
        "Скучно и сыро.",
        "От проекта ждали большего.",
        "Плохая оптимизация портит впечатление.",
        "Геймдизайн оставляет желать лучшего.",
    ]
    neutral_pool = [
        "Есть потенциал, но не дотянули.",
        "Достойный середняк без откровений.",
        "Некоторые идеи радуют, но много недочётов.",
        "Проект найдет свою аудиторию, но не всех удивит.",
    ]
    positive_pool = [
        "Свежо и увлекательно, отличный релиз!",
        "Хит! Сложно оторваться.",
        "Баланс, геймплей и подача на высоте.",
        "Пример того, как делать жанр правильно.",
    ]

    if score < 40:
        pool = negative_pool
    elif score < 70:
        pool = neutral_pool
    else:
        pool = positive_pool

    review_count = random.randint(3, 7)
    # Чтобы не повторяться, расширяем пул и перемешиваем
    pool_to_draw = pool * 2
    random.shuffle(pool_to_draw)
    return pool_to_draw[:review_count]


def calculate_sales(
    score: float, base_price: int, market_size: int, config: BalanceConfig | None = None
) -> int:
    """Оценивает продажи (копий) на основе оценки игры.

    Чем выше score, тем быстрее растёт множитель спроса. Низкие оценки
    дают минимальные продажи, а хиты бьют потолок рынка.
    """

    config = config or get_default_balance_config()

    normalized_score = max(0.0, score) / 50  # 1.0 ≈ достойная игра
    demand_multiplier = normalized_score**1.4
    demand_multiplier = max(0.05, demand_multiplier)

    potential_sales = market_size * demand_multiplier * config.base_project_income_multiplier
    # Небольшая случайность для разнообразия
    variance = random.uniform(0.9, 1.1)
    units_sold = int(potential_sales * variance)

    revenue = units_sold * base_price
    return revenue
