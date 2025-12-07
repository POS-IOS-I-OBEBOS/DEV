"""Точка входа в симулятор разработки игр."""

import argparse

from game_dev_simulator.core import (
    Employee,
    GameProject,
    GameSimulation,
    GameStudio,
    MarketTrend,
)
from game_dev_simulator.ui import GameCLI, GamePygameUI
from game_dev_simulator.ui.theme import DEFAULT_THEME, Theme


def build_default_simulation() -> GameSimulation:
    """Создаёт типовую стартовую конфигурацию студии."""

    employees = [
        Employee(
            name="Анна",
            role="programmer",
            skill_code=6,
            skill_design=3,
            skill_art=2,
            skill_sound=1,
            salary=25,
        ),
        Employee(
            name="Борис",
            role="designer",
            skill_code=2,
            skill_design=5,
            skill_art=2,
            skill_sound=1,
            salary=22,
        ),
        Employee(
            name="Вика",
            role="artist",
            skill_code=1,
            skill_design=2,
            skill_art=6,
            skill_sound=1,
            salary=20,
        ),
    ]

    project = GameProject(
        title="RPG Dream",
        genre="RPG",
        platform="PC",
        complexity=40,
    )
    project.assigned_employees.extend(employees[:2])

    studio = GameStudio(
        name="Indie Sparks",
        cash=1500,
        reputation=2,
        employees=employees,
        projects=[project],
    )
    trend = MarketTrend(trending_genres=["RPG", "Strategy"], popular_platforms=["PC"])
    return GameSimulation(studio, market_trend=trend)


def main() -> None:
    """Собирает конфигурацию студии и запускает выбранный интерфейс."""

    parser = argparse.ArgumentParser(description="Game Dev Simulator")
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Запустить красивый pygame интерфейс вместо текстового меню",
    )
    args = parser.parse_args()

    simulation = build_default_simulation()

    if args.gui:
        theme: Theme = DEFAULT_THEME
        GamePygameUI(simulation, theme=theme).run()
    else:
        GameCLI(simulation).run()


if __name__ == "__main__":
    main()
