"""Основной пакет с игровой логикой и моделями."""

from .models import Employee, GameProject, GameStudio, MarketTrend
from .simulation import GameSimulation
from .balance import (
    BalanceConfig,
    BalanceManager,
    calculate_game_score,
    calculate_sales,
    generate_reviews,
    get_default_balance_config,
)
from .events import GameEvent, handle_release_event

__all__ = [
    "Employee",
    "GameProject",
    "GameStudio",
    "MarketTrend",
    "GameSimulation",
    "BalanceConfig",
    "BalanceManager",
    "GameEvent",
    "calculate_game_score",
    "generate_reviews",
    "calculate_sales",
    "handle_release_event",
    "get_default_balance_config",
]
