"""Простой текстовый интерфейс для взаимодействия с симуляцией."""

from __future__ import annotations

from typing import Iterable, List

from game_dev_simulator.core import GameSimulation
from game_dev_simulator.core.models import Employee, GameProject
from game_dev_simulator.save import Storage, load_game, save_game


class GameCLI:
    """Текстовый интерфейс управления студией."""

    def __init__(self, simulation: GameSimulation, storage: Storage | None = None, save_file: str = "save/game_save.json") -> None:
        self.simulation = simulation
        self.storage = storage or Storage()
        self.save_file = save_file

    def run(self) -> None:
        """Основной цикл меню, пока игрок не выберет выход."""

        print("Добро пожаловать в Game Dev Simulator!")
        while True:
            print("\nГлавное меню:")
            print("1) Следующая неделя")
            print("2) Управление сотрудниками")
            print("3) Управление проектами")
            print("4) Отчёт студии")
            print("5) Сохранить игру")
            print("6) Загрузить игру")
            print("0) Выход")

            choice = input("Ваш выбор: ").strip()
            if choice == "1":
                self.simulation.run_step()
                print("Неделя завершена.")
                self._print_state_summary()
            elif choice == "2":
                self.handle_employees_menu()
            elif choice == "3":
                self.handle_projects_menu()
            elif choice == "4":
                self.show_report()
            elif choice == "5":
                save_game(self.simulation, filename=self.save_file)
                print(f"Состояние сохранено в {self.save_file}.")
            elif choice == "6":
                self._load_from_file()
            elif choice == "0":
                print("До встречи!")
                break
            else:
                print("Неизвестная команда.")

    def handle_employees_menu(self) -> None:
        """Меню управления сотрудниками: нанять, уволить, список."""

        while True:
            print("\nСотрудники:")
            print("1) Нанять сотрудника")
            print("2) Уволить сотрудника")
            print("3) Список сотрудников")
            print("0) Назад")
            choice = input("Ваш выбор: ").strip()

            if choice == "1":
                self._hire_employee()
            elif choice == "2":
                self._fire_employee()
            elif choice == "3":
                self._list_employees()
            elif choice == "0":
                break
            else:
                print("Неизвестная команда.")

    def handle_projects_menu(self) -> None:
        """Меню управления проектами: создание, назначение, прогресс."""

        while True:
            print("\nПроекты:")
            print("1) Создать новый проект")
            print("2) Назначить сотрудников на проект")
            print("3) Посмотреть прогресс проектов")
            print("0) Назад")
            choice = input("Ваш выбор: ").strip()

            if choice == "1":
                self._create_project()
            elif choice == "2":
                self._assign_employees_to_project()
            elif choice == "3":
                self._list_projects()
            elif choice == "0":
                break
            else:
                print("Неизвестная команда.")

    def show_report(self) -> None:
        """Печать сводки по студии и проектам."""

        summary = self.simulation.get_state_summary()
        print("\n=== Отчёт студии ===")
        print(f"Неделя: {summary['week']} (год {summary['year']})")
        print(f"Деньги: ${summary['cash']}")
        print(f"Репутация: {summary['reputation']}")
        print(f"Сотрудники: {len(summary['employees'])}")
        print("Активные проекты:")
        for title in summary["active_projects"]:
            print(f" - {title}")
        print("Завершённые проекты:")
        for title in summary["finished_projects"]:
            print(f" - {title}")
        print("===================\n")

    def _load_from_file(self) -> None:
        """Загружает сохранение с диска и подменяет текущую симуляцию."""

        try:
            self.simulation = load_game(filename=self.save_file)
        except FileNotFoundError:
            print("Файл сохранения не найден.")
            return
        except (OSError, ValueError) as error:
            print(f"Ошибка загрузки: {error}")
            return

        print("Состояние загружено из файла.")

    def _print_state_summary(self) -> None:
        summary = self.simulation.get_state_summary()
        print(
            f"Неделя {summary['week']} (год {summary['year']}): "
            f"касса ${summary['cash']}, репутация {summary['reputation']}"
        )

    def _hire_employee(self) -> None:
        name = input("Имя сотрудника: ").strip() or "Новичок"
        role = input("Роль (programmer/designer/artist/sound/producer): ").strip() or "programmer"
        skill_code = self._read_int("Навык кода (0-10): ", 3)
        skill_design = self._read_int("Навык дизайна (0-10): ", 3)
        skill_art = self._read_int("Навык графики (0-10): ", 3)
        skill_sound = self._read_int("Навык звука (0-10): ", 3)
        salary = self._read_int("Зарплата (в неделю): ", 20)

        employee = Employee(
            name=name,
            role=role,
            skill_code=skill_code,
            skill_design=skill_design,
            skill_art=skill_art,
            skill_sound=skill_sound,
            salary=salary,
        )
        self.simulation.studio.employees.append(employee)
        print(f"Нанят {employee.name} в роль {employee.role}.")

    def _fire_employee(self) -> None:
        if not self.simulation.studio.employees:
            print("Нет сотрудников для увольнения.")
            return

        self._list_employees()
        idx = self._read_int("Введите номер сотрудника для увольнения: ", -1)
        if 0 <= idx < len(self.simulation.studio.employees):
            fired = self.simulation.studio.employees.pop(idx)
            print(f"Сотрудник {fired.name} уволен.")
            for project in self.simulation.studio.projects:
                if fired in project.assigned_employees:
                    project.assigned_employees.remove(fired)
        else:
            print("Некорректный номер.")

    def _list_employees(self) -> None:
        if not self.simulation.studio.employees:
            print("Сотрудников нет.")
            return
        print("Текущие сотрудники:")
        for i, employee in enumerate(self.simulation.studio.employees):
            print(
                f"[{i}] {employee.name} — {employee.role}, зарплата ${employee.salary}, "
                f"усталость {employee.fatigue}"
            )

    def _create_project(self) -> None:
        title = input("Название проекта: ").strip() or "Новый проект"
        genre = input("Жанр: ").strip() or "Arcade"
        platform = input("Платформа: ").strip() or "PC"
        complexity = self._read_int("Сложность (чем выше, тем дольше): ", 20)
        project = GameProject(
            title=title,
            genre=genre,
            platform=platform,
            complexity=complexity,
        )
        self.simulation.studio.projects.append(project)
        print(f"Проект {title} создан.")

    def _assign_employees_to_project(self) -> None:
        if not self.simulation.studio.projects:
            print("Нет проектов для назначения.")
            return
        self._list_projects()
        proj_idx = self._read_int("Введите номер проекта: ", -1)
        if not 0 <= proj_idx < len(self.simulation.studio.projects):
            print("Некорректный номер проекта.")
            return
        project = self.simulation.studio.projects[proj_idx]
        self._list_employees()
        raw = input("Введите номера сотрудников через запятую: ").strip()
        indices = self._parse_indices(raw, len(self.simulation.studio.employees))
        for idx in indices:
            employee = self.simulation.studio.employees[idx]
            if employee not in project.assigned_employees:
                project.assigned_employees.append(employee)
        print(f"Назначены сотрудники на проект {project.title}.")

    def _list_projects(self) -> None:
        if not self.simulation.studio.projects:
            print("Активных проектов нет.")
            return
        print("Текущие проекты:")
        for i, project in enumerate(self.simulation.studio.projects):
            print(
                f"[{i}] {project.title} — статус {project.status}, "
                f"прогресс {project.progress:.1f}%, сложность {project.complexity}"
            )

    def _read_int(self, prompt: str, default: int) -> int:
        try:
            value = int(input(prompt).strip())
        except ValueError:
            value = default
        return value

    def _parse_indices(self, raw: str, upper: int) -> List[int]:
        result: List[int] = []
        for part in raw.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                idx = int(part)
            except ValueError:
                continue
            if 0 <= idx < upper:
                result.append(idx)
        return result


def run_cli(simulation: GameSimulation, turns: int = 3) -> None:
    """Совместимость: запускает короткий сценарий через новое меню."""

    cli = GameCLI(simulation)
    for _ in range(turns):
        simulation.run_step()
        cli._print_state_summary()
    print("Демо завершено\n")


__all__ = ["GameCLI", "run_cli"]
