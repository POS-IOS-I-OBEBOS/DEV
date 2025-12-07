"""Простой визуальный интерфейс на pygame для отображения состояния симуляции."""

from __future__ import annotations

from typing import Tuple

from game_dev_simulator.core import GameSimulation


Color = Tuple[int, int, int]


class GamePygameUI:
    """Отображает состояние студии в окне pygame и позволяет листать недели."""

    def __init__(self, width: int = 900, height: int = 600) -> None:
        self.width = width
        self.height = height
        self.background: Color = (26, 28, 34)
        self.text_color: Color = (230, 230, 230)
        self.accent: Color = (96, 169, 255)
        self.progress_bg: Color = (70, 70, 80)

    def run(self, simulation: GameSimulation) -> None:
        """Запускает цикл pygame и отображает данные симуляции."""

        import pygame

        pygame.init()
        screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Game Dev Simulator — pygame")
        clock = pygame.time.Clock()

        title_font = pygame.font.SysFont("arial", 28)
        text_font = pygame.font.SysFont("arial", 20)
        small_font = pygame.font.SysFont("arial", 16)

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key in {pygame.K_ESCAPE, pygame.K_q}:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key in {pygame.K_SPACE, pygame.K_RETURN}:
                    simulation.run_step()

            screen.fill(self.background)

            self._draw_header(screen, simulation, title_font, small_font)
            self._draw_projects(screen, simulation, text_font, small_font)
            self._draw_employees(screen, simulation, text_font, small_font)
            self._draw_help(screen, small_font)

            pygame.display.flip()
            clock.tick(30)

        pygame.quit()

    def _draw_header(self, screen: "pygame.Surface", simulation: GameSimulation, title_font, small_font) -> None:
        summary = simulation.get_state_summary()
        header_text = f"Неделя {summary['week']} / Год {summary['year']}"
        cash_text = f"Касса: ${summary['cash']} | Репутация: {summary['reputation']}"

        header_surf = title_font.render(header_text, True, self.text_color)
        cash_surf = small_font.render(cash_text, True, self.text_color)
        screen.blit(header_surf, (20, 15))
        screen.blit(cash_surf, (20, 50))

    def _draw_projects(self, screen: "pygame.Surface", simulation: GameSimulation, text_font, small_font) -> None:
        y_offset = 90
        screen.blit(text_font.render("Проекты", True, self.text_color), (20, y_offset))
        y_offset += 30
        bar_width = self.width // 2 - 60
        bar_height = 18

        for project in simulation.studio.projects:
            title = f"{project.title} ({project.genre}/{project.platform})"
            status = f"{project.progress:.1f}% — статус: {project.status}"
            title_surf = small_font.render(title, True, self.text_color)
            status_surf = small_font.render(status, True, self.text_color)
            screen.blit(title_surf, (20, y_offset))
            screen.blit(status_surf, (20, y_offset + 18))

            progress_ratio = max(0.0, min(1.0, project.progress / 100.0))
            filled_width = int(bar_width * progress_ratio)
            bar_rect = (20, y_offset + 40, bar_width, bar_height)
            fill_rect = (20, y_offset + 40, filled_width, bar_height)
            import pygame  # локальный импорт для избежания глобальной зависимости

            pygame.draw.rect(screen, self.progress_bg, bar_rect, border_radius=4)
            pygame.draw.rect(screen, self.accent, fill_rect, border_radius=4)

            y_offset += 70

        if not simulation.studio.projects:
            screen.blit(small_font.render("Нет активных проектов", True, self.text_color), (20, y_offset))

    def _draw_employees(self, screen: "pygame.Surface", simulation: GameSimulation, text_font, small_font) -> None:
        x_start = self.width // 2 + 20
        y_offset = 90
        screen.blit(text_font.render("Сотрудники", True, self.text_color), (x_start, y_offset))
        y_offset += 30

        for employee in simulation.studio.employees:
            summary = f"{employee.name} — {employee.role}"
            fatigue = f"Усталость: {employee.fatigue}%"
            summary_surf = small_font.render(summary, True, self.text_color)
            fatigue_surf = small_font.render(fatigue, True, self.text_color)
            screen.blit(summary_surf, (x_start, y_offset))
            screen.blit(fatigue_surf, (x_start, y_offset + 18))

            bar_width = self.width // 2 - 80
            bar_height = 12
            progress_ratio = max(0.0, min(1.0, employee.fatigue / 100.0))
            filled_width = int(bar_width * progress_ratio)
            bar_rect = (x_start, y_offset + 38, bar_width, bar_height)
            fill_rect = (x_start, y_offset + 38, filled_width, bar_height)
            import pygame  # локальный импорт для избежания глобальной зависимости

            pygame.draw.rect(screen, self.progress_bg, bar_rect, border_radius=3)
            pygame.draw.rect(screen, (255, 140, 105), fill_rect, border_radius=3)

            y_offset += 70

        if not simulation.studio.employees:
            screen.blit(small_font.render("Нет сотрудников", True, self.text_color), (x_start, y_offset))

    def _draw_help(self, screen: "pygame.Surface", small_font) -> None:
        hints = [
            "Пробел / Enter — следующая неделя",
            "Esc или Q — выход",
        ]
        y = self.height - 60
        for hint in hints:
            hint_surf = small_font.render(hint, True, self.text_color)
            screen.blit(hint_surf, (20, y))
            y += 18


__all__ = ["GamePygameUI"]
