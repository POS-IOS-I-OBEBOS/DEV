"""Точка входа в симулятор разработки игр."""

import sys

from game_dev_simulator.core import (
    Employee,
    GameProject,
    GameSimulation,
    GameStudio,
    MarketTrend,
)
from game_dev_simulator.ui import GameCLI


def main() -> None:
    """Собирает конфигурацию студии и запускает текстовый интерфейс."""

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
    simulation = GameSimulation(studio, market_trend=trend)

    ui_mode = "cli"
    for arg in sys.argv[1:]:
        lowered = arg.lower()
        if lowered in {"--ui=pygame", "--pygame", "pygame"}:
            ui_mode = "pygame"
            break

    if ui_mode == "pygame":
        from game_dev_simulator.ui import GamePygameUI

        GamePygameUI().run(simulation)
    else:
        GameCLI(simulation).run()


if __name__ == "__main__":
    main()
