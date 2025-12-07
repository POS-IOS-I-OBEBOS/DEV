"""Современный pygame-UI для управления студией Game Dev Simulator.

Содержит панели сотрудников и проектов, лог событий, кнопки действий,
авто-симуляцию и модальные диалоги создания проектов/сотрудников.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from random import randint
from typing import Callable, Dict, List, Optional, Tuple

import pygame

from game_dev_simulator.core import Employee, GameProject, GameSimulation
from game_dev_simulator.save.storage import load_game, save_game
from game_dev_simulator.ui.theme import DEFAULT_THEME, Theme


@dataclass
class UIButton:
    """Простая прямоугольная кнопка с подсветкой наведения."""

    rect: pygame.Rect
    text: str
    callback: Callable[[], None]

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, *, theme: Theme, hovered: bool, active: bool = False) -> None:
        bg = theme.BUTTON_BG_ACTIVE if active else (theme.BUTTON_BG_HOVER if hovered else theme.BUTTON_BG)
        pygame.draw.rect(surface, bg, self.rect, border_radius=8)
        if hovered:
            pygame.draw.rect(surface, theme.HOVER_BORDER, self.rect, width=1, border_radius=8)
        label = font.render(self.text, True, theme.TEXT)
        surface.blit(label, label.get_rect(center=self.rect.center))

    def is_hovered(self, pos: Tuple[int, int]) -> bool:
        return self.rect.collidepoint(pos)


@dataclass
class InputField:
    """Поле ввода для модальных окон."""

    label: str
    value: str = ""
    numeric: bool = False
    active: bool = False
    rect: Optional[pygame.Rect] = None


class ModalDialog:
    """Базовое модальное окно с несколькими полями."""

    def __init__(self, title: str, fields: List[InputField], on_submit: Callable[[List[str]], None], theme: Theme) -> None:
        self.title = title
        self.fields = fields
        self.on_submit = on_submit
        self.theme = theme
        self.open = True
        self.ok_button: Optional[UIButton] = None
        self.cancel_button: Optional[UIButton] = None

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.open = False
                return
            if event.key == pygame.K_RETURN:
                self._confirm()
                return
            for field in self.fields:
                if field.active:
                    if event.key == pygame.K_BACKSPACE:
                        field.value = field.value[:-1]
                    else:
                        char = event.unicode
                        if not char:
                            return
                        if field.numeric and not char.isdigit():
                            return
                        field.value += char
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.ok_button and self.ok_button.is_hovered(event.pos):
                self._confirm()
                return
            if self.cancel_button and self.cancel_button.is_hovered(event.pos):
                self.open = False
                return
            for field in self.fields:
                if field.rect and field.rect.collidepoint(event.pos):
                    self._set_active(field)
                    return
            # щелчок вне полей снимает выделение
            for f in self.fields:
                f.active = False

    def _set_active(self, field: InputField) -> None:
        for f in self.fields:
            f.active = False
        field.active = True

    def _confirm(self) -> None:
        values = [f.value for f in self.fields]
        self.on_submit(values)
        self.open = False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, title_font: pygame.font.Font) -> None:
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, self.theme.OVERLAY_ALPHA))
        surface.blit(overlay, (0, 0))

        box_width, box_height = 520, 360
        box_rect = pygame.Rect(
            (surface.get_width() - box_width) // 2,
            (surface.get_height() - box_height) // 2,
            box_width,
            box_height,
        )
        pygame.draw.rect(surface, self.theme.PANEL, box_rect, border_radius=12)
        pygame.draw.rect(surface, self.theme.ACCENT, box_rect, width=2, border_radius=12)

        title_surf = title_font.render(self.title, True, self.theme.TEXT)
        surface.blit(title_surf, (box_rect.x + 20, box_rect.y + 16))

        y = box_rect.y + 70
        field_rects: List[pygame.Rect] = []
        for field in self.fields:
            label_surf = font.render(field.label, True, self.theme.SUBTEXT)
            surface.blit(label_surf, (box_rect.x + 20, y))
            input_rect = pygame.Rect(box_rect.x + 20, y + 24, box_width - 40, 32)
            pygame.draw.rect(surface, self.theme.PANEL_DARK, input_rect, border_radius=6)
            border_color = self.theme.ACCENT if field.active else self.theme.PROGRESS_BG
            pygame.draw.rect(surface, border_color, input_rect, width=2, border_radius=6)
            text_surf = font.render(field.value or " ", True, self.theme.TEXT)
            surface.blit(text_surf, (input_rect.x + 8, input_rect.y + 6))
            field.rect = input_rect
            field_rects.append(input_rect)
            y += 68

        btn_w = 140
        btn_h = 42
        btn_y = box_rect.bottom - btn_h - 20
        ok_rect = pygame.Rect(box_rect.x + box_width - btn_w * 2 - 30, btn_y, btn_w, btn_h)
        cancel_rect = pygame.Rect(box_rect.x + box_width - btn_w - 20, btn_y, btn_w, btn_h)
        self.ok_button = UIButton(ok_rect, "OK", lambda: None)
        self.cancel_button = UIButton(cancel_rect, "Отмена", lambda: None)

        mouse_pos = pygame.mouse.get_pos()
        self.ok_button.draw(surface, font, theme=self.theme, hovered=self.ok_button.is_hovered(mouse_pos))
        self.cancel_button.draw(surface, font, theme=self.theme, hovered=self.cancel_button.is_hovered(mouse_pos))

        ok_label = font.render("OK", True, self.theme.TEXT)
        cancel_label = font.render("Отмена", True, self.theme.TEXT)
        surface.blit(ok_label, ok_label.get_rect(center=ok_rect.center))
        surface.blit(cancel_label, cancel_label.get_rect(center=cancel_rect.center))


class ProjectDialog(ModalDialog):
    """Диалог создания нового проекта."""

    def __init__(self, on_submit: Callable[[List[str]], None], theme: Theme):
        fields = [
            InputField("Название"),
            InputField("Жанр"),
            InputField("Платформа"),
            InputField("Сложность", numeric=True),
        ]
        super().__init__("Новый проект", fields, on_submit, theme)


class EmployeeDialog(ModalDialog):
    """Диалог найма нового сотрудника."""

    def __init__(self, on_submit: Callable[[List[str]], None], theme: Theme):
        fields = [
            InputField("Имя"),
            InputField("Роль"),
            InputField("Зарплата", numeric=True),
        ]
        super().__init__("Новый сотрудник", fields, on_submit, theme)


class OfficeView:
    """Простая 2D-сцена офиса со схематичными зонами и аватарами сотрудников."""

    def __init__(self, rect: pygame.Rect, simulation: GameSimulation, theme: Theme) -> None:
        self.rect = rect
        self.simulation = simulation
        self.theme = theme
        self.avatar_slots: List[Tuple[pygame.Rect, int]] = []
        self.selected_employee: Optional[int] = None

        # Позиции для плавного движения сотрудников в офисе
        self.employee_positions: Dict[Employee, pygame.Vector2] = {}
        self.employee_target_positions: Dict[Employee, pygame.Vector2] = {}
        self.employee_home_positions: Dict[Employee, pygame.Vector2] = {}
        self.employee_state: Dict[Employee, str] = {}
        self.employee_timers: Dict[Employee, float] = {}
        self.rest_change_interval = 3.0
        self.move_speed = 130.0  # пикселей в секунду

        self._ensure_positions()  # первичная раскладка рабочих мест

    def set_selected_employee(self, idx: Optional[int]) -> None:
        """Синхронизирует выделение с панелью сотрудников."""

        self.selected_employee = idx

    def update(self, dt: float) -> None:
        """Плавно двигаем аватары к таргетам и переключаем состояния отдыха/работы."""

        self._ensure_positions()

        zones = self._role_zone()
        rest_zone = zones["rest"]
        rest_slots = self._layout_positions(rest_zone, max(1, len(self.simulation.studio.employees)))

        for idx, emp in enumerate(self.simulation.studio.employees):
            state = self.employee_state.get(emp, "working")
            timer = self.employee_timers.get(emp, 0.0) + dt
            self.employee_timers[emp] = timer

            # Отправляем сильно уставших сотрудников отдыхать раз в несколько секунд
            if state == "working" and emp.fatigue > 80 and timer >= self.rest_change_interval:
                self.employee_state[emp] = "resting"
                self.employee_timers[emp] = 0.0
                target = rest_slots[idx % len(rest_slots)]
                self.employee_target_positions[emp] = pygame.Vector2(target)
            # Возвращаем бодрых сотрудников за столы
            elif state == "resting" and emp.fatigue < 30 and timer >= self.rest_change_interval:
                self.employee_state[emp] = "working"
                self.employee_timers[emp] = 0.0
                self.employee_target_positions[emp] = self.employee_home_positions.get(
                    emp, self.employee_target_positions.get(emp, pygame.Vector2(rest_zone.center))
                )

            # Плавное перемещение к целевой точке
            pos = self.employee_positions.get(emp, pygame.Vector2(rest_zone.center))
            target = self.employee_target_positions.get(emp, pos)
            direction = target - pos
            distance = direction.length()
            if distance > 0:
                direction.scale_to_length(min(distance, self.move_speed * dt))
                pos += direction
                self.employee_positions[emp] = pos

    def _role_zone(self) -> Dict[str, pygame.Rect]:
        """Возвращает расположение зон офиса для разных ролей и отдыха."""

        pad = self.theme.PANEL_PADDING
        inner = self.rect.inflate(-pad * 2, -pad * 2)
        zone_height = inner.height // 3
        rest_height = max(80, int(zone_height * 0.8))
        # Основные рабочие зоны: программисты, дизайн/арт, звук/продюсеры
        return {
            "programmer": pygame.Rect(inner.x, inner.y, inner.width, zone_height),
            "designer": pygame.Rect(inner.x, inner.y + zone_height, inner.width // 2, zone_height),
            "artist": pygame.Rect(inner.x + inner.width // 2, inner.y + zone_height, inner.width // 2, zone_height),
            "sound": pygame.Rect(inner.x, inner.y + zone_height * 2, inner.width // 2, zone_height - rest_height // 2),
            "producer": pygame.Rect(
                inner.x + inner.width // 2, inner.y + zone_height * 2, inner.width // 2, zone_height - rest_height // 2
            ),
            "rest": pygame.Rect(inner.x, inner.bottom - rest_height, inner.width, rest_height),
        }

    def _role_label(self, role: str) -> str:
        return {
            "programmer": "Зона программистов",
            "designer": "Дизайн / арт",
            "artist": "Дизайн / арт",
            "sound": "Студия звука",
            "producer": "Продюсерская",
        }.get(role, "Офис")

    def _avatar_color(self, fatigue: float) -> Tuple[int, int, int]:
        if fatigue > 70:
            return self.theme.ERROR
        if fatigue > 30:
            return self.theme.WARNING
        return self.theme.SUCCESS

    def _layout_positions(self, zone: pygame.Rect, count: int) -> List[Tuple[int, int]]:
        """Располагаем аватары сеткой внутри зоны."""

        positions: List[Tuple[int, int]] = []
        cols = max(1, min(5, zone.width // 120))
        spacing_x = zone.width // (cols + 1)
        rows = (count + cols - 1) // cols
        spacing_y = max(60, zone.height // (rows + 1))
        idx = 0
        for r in range(rows):
            y = zone.y + spacing_y * (r + 1)
            for c in range(cols):
                if idx >= count:
                    break
                x = zone.x + spacing_x * (c + 1)
                positions.append((x, y))
                idx += 1
        return positions

    def _ensure_positions(self) -> None:
        """Подбираем рабочие места и таргеты для всех сотрудников."""

        zones = self._role_zone()
        role_buckets: Dict[str, List[Employee]] = {}
        for emp in self.simulation.studio.employees:
            role_buckets.setdefault(emp.role, []).append(emp)

        # Раскладываем сотрудников по рабочим зонам и сохраняем "домашние" позиции
        for role, emps in role_buckets.items():
            zone = zones.get(role, self.rect)
            positions = self._layout_positions(zone, len(emps))
            for emp, pos in zip(emps, positions):
                home_vec = pygame.Vector2(pos)
                if emp not in self.employee_home_positions:
                    # Небольшой сдвиг, чтобы аватары выглядели живее
                    jitter = pygame.Vector2(randint(-6, 6), randint(-6, 6))
                    self.employee_home_positions[emp] = home_vec + jitter
                if emp not in self.employee_positions:
                    self.employee_positions[emp] = self.employee_home_positions[emp]
                if emp not in self.employee_target_positions:
                    self.employee_target_positions[emp] = self.employee_home_positions[emp]
                if emp not in self.employee_state:
                    self.employee_state[emp] = "working"
                if emp not in self.employee_timers:
                    self.employee_timers[emp] = 0.0

        # Удаляем записи для уволенных сотрудников
        alive = set(self.simulation.studio.employees)
        for mapping in (
            self.employee_positions,
            self.employee_target_positions,
            self.employee_home_positions,
            self.employee_state,
            self.employee_timers,
        ):
            for emp in list(mapping.keys()):
                if emp not in alive:
                    mapping.pop(emp, None)

    def draw(self, surface: pygame.Surface) -> None:
        """Рисуем фон офиса, зоны и аватары сотрудников."""

        pygame.draw.rect(surface, self.theme.PANEL_DARK, self.rect, border_radius=12)

        zones = self._role_zone()
        self.avatar_slots.clear()
        role_buckets: Dict[str, List[Employee]] = {}
        for emp in self.simulation.studio.employees:
            role_buckets.setdefault(emp.role, []).append(emp)

        # Рисуем зоны
        for role, zone in zones.items():
            pygame.draw.rect(surface, self.theme.PANEL, zone, border_radius=10)
            label = self._role_label(role)
            font = pygame.font.SysFont(self.theme.FONT_NAME, self.theme.FONT_SIZE)
            surface.blit(font.render(label, True, self.theme.SUBTEXT), (zone.x + 8, zone.y + 6))

        # Раскладываем аватары по ролям
        for role, emps in role_buckets.items():
            zone = zones.get(role, self.rect)
            for emp in emps:
                color = self._avatar_color(emp.fatigue)
                avatar_rect = pygame.Rect(0, 0, 28, 28)
                avatar_rect.center = self.employee_positions.get(emp, pygame.Vector2(zone.center))
                pygame.draw.circle(surface, color, avatar_rect.center, 14)
                pygame.draw.circle(surface, self.theme.PANEL_DARK, avatar_rect.center, 14, width=2)

                if self.selected_employee is not None and 0 <= self.selected_employee < len(self.simulation.studio.employees):
                    if self.simulation.studio.employees[self.selected_employee] is emp:
                        pygame.draw.circle(surface, self.theme.ACCENT, avatar_rect.center, 17, width=2)

                font = pygame.font.SysFont(self.theme.FONT_NAME, self.theme.FONT_SIZE - 2)
                name_text = font.render(emp.name, True, self.theme.TEXT)
                project = self.get_employee_project(emp)
                if self.employee_state.get(emp) == "resting":
                    status_line = "Отдыхает"
                elif project:
                    status_line = f"Работает над {project.title}"
                else:
                    status_line = emp.role

                status_text = font.render(status_line, True, self.theme.SUBTEXT)
                surface.blit(name_text, (avatar_rect.centerx + 18, avatar_rect.centery - 10))
                surface.blit(status_text, (avatar_rect.centerx + 18, avatar_rect.centery + 6))

                self.avatar_slots.append((avatar_rect, self.simulation.studio.employees.index(emp)))

    def handle_click(self, pos: Tuple[int, int]) -> Optional[int]:
        """Возвращает индекс сотрудника при клике по аватару."""

        for rect, idx in self.avatar_slots:
            if rect.collidepoint(pos):
                self.selected_employee = idx
                return idx
        return None

    def get_employee_project(self, employee: Employee) -> Optional[GameProject]:
        """Ищем проект, к которому закреплён сотрудник (для подписи статуса)."""

        for project in self.simulation.studio.projects:
            if employee in project.assigned_employees:
                return project
        return None


class GamePygameUI:
    """Красивый дашборд на pygame поверх GameSimulation."""

    def __init__(self, simulation: GameSimulation, theme: Theme | None = None) -> None:
        self.simulation = simulation
        self.theme = theme or DEFAULT_THEME
        self.employee_slots: List[Tuple[pygame.Rect, int]] = []
        self.project_slots: List[Tuple[pygame.Rect, int]] = []
        self.center_project_slots: List[Tuple[pygame.Rect, int]] = []
        self.selected_employee: Optional[int] = None
        self.selected_project: Optional[int] = None
        self.center_mode: str = "office"
        self.center_tabs: List[Tuple[pygame.Rect, str]] = []
        self.buttons: List[UIButton] = []
        self.dialog: Optional[ModalDialog] = None
        self.logs: List[Dict[str, float | str]] = []
        self.max_logs = 50
        self.rendered_progress: Dict[int, float] = {}
        self.auto_simulation_enabled = False
        self.auto_timer = 0.0
        self.auto_interval = 1.5
        self.employees_scroll = 0
        self.running = True
        center_x = int(self.theme.WINDOW_WIDTH * 0.3)
        center_w = int(self.theme.WINDOW_WIDTH * 0.4)
        center_h = self.theme.WINDOW_HEIGHT - self.theme.STATUS_HEIGHT - self.theme.LOG_HEIGHT
        center_rect = pygame.Rect(center_x, self.theme.STATUS_HEIGHT, center_w, center_h)
        self.office_rect_base = center_rect
        self.office_view = OfficeView(center_rect.copy(), self.simulation, self.theme)

    # Основной цикл ------------------------------------------------------
    def run(self) -> None:
        pygame.init()
        screen = pygame.display.set_mode((self.theme.WINDOW_WIDTH, self.theme.WINDOW_HEIGHT))
        pygame.display.set_caption("Game Dev Simulator — Управление студией")
        clock = pygame.time.Clock()

        font = pygame.font.SysFont(self.theme.FONT_NAME, self.theme.FONT_SIZE)
        title_font = pygame.font.SysFont(self.theme.FONT_NAME, self.theme.FONT_SIZE_TITLE, bold=True)

        self.add_log_message("Добро пожаловать в Game Dev Simulator!")
        last_time = time.time()
        while self.running:
            now = time.time()
            dt = now - last_time
            last_time = now

            self.handle_events()
            self.update(dt)
            self.draw(screen, font, title_font)

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

    # Обновление логики --------------------------------------------------
    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            if self.dialog:
                self.dialog.handle_event(event)
                if not self.dialog.open:
                    self.dialog = None
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                if event.key == pygame.K_SPACE:
                    self._do_next_week()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.handle_mouse_click(event.pos)
                elif event.button == 4:  # scroll up
                    self.employees_scroll = min(self.employees_scroll + self.theme.SCROLL_STEP, 0)
                elif event.button == 5:  # scroll down
                    self.employees_scroll -= self.theme.SCROLL_STEP

    def update(self, dt: float) -> None:
        # Обновляем возраст сообщений лога для легкого затухания
        for log in self.logs:
            log["age"] = log.get("age", 0.0) + dt

        # Плавно подтягиваем визуальный прогресс проектов
        for project in list(self.simulation.studio.projects):
            target = project.progress
            key = id(project)
            current = self.rendered_progress.get(key, target)
            if abs(current - target) < 0.1:
                self.rendered_progress[key] = target
            else:
                step = 40 * dt
                self.rendered_progress[key] = current + step if current < target else current - step

        # Авто-симуляция
        if self.auto_simulation_enabled:
            self.auto_timer += dt
            if self.auto_timer >= self.auto_interval:
                self.auto_timer = 0.0
                self._do_next_week()

        # Обновляем анимации офиса (движение аватаров, смена состояний)
        self.office_view.update(dt)

    # Рисование ----------------------------------------------------------
    def draw(self, surface: pygame.Surface, font: pygame.font.Font, title_font: pygame.font.Font) -> None:
        surface.fill(self.theme.BG)
        self.draw_status_bar(surface, font, title_font)
        self.draw_employees_panel(surface, font, title_font)
        self.draw_center(surface, font, title_font)
        self.draw_actions_panel(surface, font, title_font)
        self.draw_log_panel(surface, font)
        if self.dialog:
            self.dialog.draw(surface, font, title_font)

    def draw_status_bar(self, surface: pygame.Surface, font: pygame.font.Font, title_font: pygame.font.Font) -> None:
        bar_rect = pygame.Rect(0, 0, self.theme.WINDOW_WIDTH, self.theme.STATUS_HEIGHT)
        pygame.draw.rect(surface, self.theme.STATUS_BG, bar_rect)

        summary = self.simulation.get_state_summary()
        left = title_font.render(summary.get("studio", "Студия"), True, self.theme.TEXT)
        center = title_font.render(f"Год {summary['year']} · Неделя {summary['week']}", True, self.theme.TEXT)
        right_cash = title_font.render(f"💰 {summary['cash']}", True, self.theme.TEXT)
        right_rep = title_font.render(f"⭐ {summary['reputation']}", True, self.theme.TEXT)

        surface.blit(left, (self.theme.PANEL_PADDING, 16))
        surface.blit(center, center.get_rect(center=(self.theme.WINDOW_WIDTH // 2, 16 + center.get_height() // 2)))
        surface.blit(right_cash, (self.theme.WINDOW_WIDTH - right_cash.get_width() - 180, 16))
        surface.blit(right_rep, (self.theme.WINDOW_WIDTH - right_rep.get_width() - 24, 16))

    def draw_employees_panel(self, surface: pygame.Surface, font: pygame.font.Font, title_font: pygame.font.Font) -> None:
        width = int(self.theme.WINDOW_WIDTH * 0.3)
        height = self.theme.WINDOW_HEIGHT - self.theme.STATUS_HEIGHT - self.theme.LOG_HEIGHT
        panel_rect = pygame.Rect(0, self.theme.STATUS_HEIGHT, width, height)
        pygame.draw.rect(surface, self.theme.PANEL, panel_rect)

        header = title_font.render("Сотрудники", True, self.theme.TEXT)
        surface.blit(header, (panel_rect.x + self.theme.PANEL_PADDING, panel_rect.y + self.theme.PANEL_PADDING))

        self.employee_slots.clear()
        start_y = panel_rect.y + self.theme.PANEL_PADDING * 2 + header.get_height() + self.employees_scroll
        card_height = 96
        for idx, emp in enumerate(self.simulation.studio.employees):
            card_rect = pygame.Rect(
                panel_rect.x + self.theme.PANEL_PADDING,
                start_y + idx * (card_height + self.theme.CARD_PADDING),
                width - self.theme.PANEL_PADDING * 2,
                card_height,
            )
            if card_rect.bottom < panel_rect.y + self.theme.PANEL_PADDING or card_rect.y > panel_rect.bottom:
                continue
            self.draw_employee_card(surface, font, emp, card_rect, selected=idx == self.selected_employee)
            self.employee_slots.append((card_rect, idx))

        # Пустое состояние
        if not self.simulation.studio.employees:
            empty = font.render("Нет сотрудников", True, self.theme.SUBTEXT)
            surface.blit(empty, (panel_rect.x + self.theme.PANEL_PADDING, panel_rect.y + 80))

    def draw_employee_card(self, surface: pygame.Surface, font: pygame.font.Font, emp: Employee, rect: pygame.Rect, *, selected: bool) -> None:
        pygame.draw.rect(surface, self.theme.PANEL_DARK, rect, border_radius=10)
        if selected:
            pygame.draw.rect(surface, self.theme.ACCENT, rect, width=2, border_radius=10)
        name = font.render(emp.name, True, self.theme.TEXT)
        role = font.render(f"{emp.role} · зп {emp.salary}", True, self.theme.SUBTEXT)
        surface.blit(name, (rect.x + self.theme.CARD_PADDING, rect.y + self.theme.CARD_PADDING))
        surface.blit(role, (rect.x + self.theme.CARD_PADDING, rect.y + self.theme.CARD_PADDING + 22))

        # Усталость в виде полосы
        bar_bg = pygame.Rect(rect.x + self.theme.CARD_PADDING, rect.bottom - 24, rect.width - self.theme.CARD_PADDING * 2, 12)
        pygame.draw.rect(surface, self.theme.PROGRESS_BG, bar_bg, border_radius=6)
        bar_width = int(bar_bg.width * min(1.0, emp.fatigue / 100))
        bar_fg = pygame.Rect(bar_bg.x, bar_bg.y, bar_width, bar_bg.height)
        pygame.draw.rect(surface, self.theme.WARNING if emp.fatigue > 70 else self.theme.PROGRESS_ACTIVE, bar_fg, border_radius=6)
        fatigue_label = font.render(f"Усталость: {emp.fatigue}%", True, self.theme.SUBTEXT)
        surface.blit(fatigue_label, (bar_bg.x, bar_bg.y - 18))

    def draw_center(self, surface: pygame.Surface, font: pygame.font.Font, title_font: pygame.font.Font) -> None:
        """Центральная зона с переключаемым видом: офис или проекты."""

        area = self.office_rect_base
        pygame.draw.rect(surface, self.theme.PANEL, area)

        # Вкладки над центральной областью
        tab_height = self.theme.BUTTON_HEIGHT
        tab_width = 130
        tab_y = area.y + self.theme.PANEL_PADDING
        tab_x = area.x + self.theme.PANEL_PADDING
        tabs = [("office", "Офис"), ("projects", "Проекты")]
        self.center_tabs.clear()
        mouse_pos = pygame.mouse.get_pos()
        for idx, (mode, label) in enumerate(tabs):
            rect = pygame.Rect(tab_x + idx * (tab_width + self.theme.PANEL_PADDING), tab_y, tab_width, tab_height)
            active = self.center_mode == mode
            hovered = rect.collidepoint(mouse_pos)
            bg = self.theme.BUTTON_BG_ACTIVE if active else (self.theme.BUTTON_BG_HOVER if hovered else self.theme.BUTTON_BG)
            pygame.draw.rect(surface, bg, rect, border_radius=10)
            pygame.draw.rect(surface, self.theme.ACCENT if active else self.theme.PANEL_DARK, rect, width=2, border_radius=10)
            text_surf = font.render(label, True, self.theme.TEXT)
            surface.blit(text_surf, text_surf.get_rect(center=rect.center))
            self.center_tabs.append((rect, mode))

        content_rect = area.inflate(-self.theme.PANEL_PADDING * 2, -self.theme.PANEL_PADDING * 3)
        content_rect.y = tab_y + tab_height + self.theme.PANEL_PADDING
        content_rect.height = area.bottom - content_rect.y - self.theme.PANEL_PADDING

        if self.center_mode == "office":
            self.draw_office(surface, font, title_font, content_rect)
        else:
            self.draw_projects_center(surface, font, title_font, content_rect)

    def draw_office(
        self, surface: pygame.Surface, font: pygame.font.Font, title_font: pygame.font.Font, content_rect: pygame.Rect
    ) -> None:
        """Центральная сцена офиса с зонами и аватарами сотрудников."""

        header = title_font.render("Офис", True, self.theme.TEXT)
        surface.blit(header, (content_rect.x, content_rect.y))

        # Небольшая подпись под заголовком
        sub = font.render("Наблюдайте за командой и кликайте по людям для выбора", True, self.theme.SUBTEXT)
        surface.blit(sub, (content_rect.x, content_rect.y + header.get_height() + 6))

        office_area = content_rect.inflate(0, -header.get_height() - self.theme.PANEL_PADDING * 2)
        office_area.y = content_rect.y + header.get_height() + self.theme.PANEL_PADDING * 2
        self.office_view.rect = office_area

        self.office_view.draw(surface)

    def draw_projects_center(
        self, surface: pygame.Surface, font: pygame.font.Font, title_font: pygame.font.Font, content_rect: pygame.Rect
    ) -> None:
        """Отображение списка проектов в центральной области."""

        header = title_font.render("Проекты", True, self.theme.TEXT)
        surface.blit(header, (content_rect.x, content_rect.y))
        sub = font.render("Прогресс и статус активных игр", True, self.theme.SUBTEXT)
        surface.blit(sub, (content_rect.x, content_rect.y + header.get_height() + 6))

        list_rect = content_rect.inflate(-self.theme.PANEL_PADDING, -header.get_height() - self.theme.PANEL_PADDING * 3)
        list_rect.y = content_rect.y + header.get_height() + self.theme.PANEL_PADDING * 2

        self.center_project_slots.clear()
        y = list_rect.y
        card_height = 96
        for idx, project in enumerate(self.simulation.studio.projects):
            rect = pygame.Rect(list_rect.x, y, list_rect.width, card_height)
            self._draw_project_overview(surface, font, project, rect, selected=idx == self.selected_project)
            self.center_project_slots.append((rect, idx))
            y += card_height + self.theme.CARD_PADDING

        if not self.simulation.studio.projects:
            empty = font.render("Нет активных проектов", True, self.theme.SUBTEXT)
            surface.blit(empty, (list_rect.x, list_rect.y))

    def _draw_project_overview(self, surface: pygame.Surface, font: pygame.font.Font, project: GameProject, rect: pygame.Rect, *, selected: bool) -> None:
        """Компактная карточка проекта в правой колонке действий."""

        pygame.draw.rect(surface, self.theme.PANEL_DARK, rect, border_radius=8)
        if selected:
            pygame.draw.rect(surface, self.theme.ACCENT, rect, width=2, border_radius=8)

        title = font.render(project.title, True, self.theme.TEXT)
        meta = font.render(f"{project.genre} · {project.platform} · {project.status}", True, self.theme.SUBTEXT)
        surface.blit(title, (rect.x + self.theme.CARD_PADDING, rect.y + self.theme.CARD_PADDING))
        surface.blit(meta, (rect.x + self.theme.CARD_PADDING, rect.y + self.theme.CARD_PADDING + 20))

        bar_bg = pygame.Rect(rect.x + self.theme.CARD_PADDING, rect.bottom - 22, rect.width - self.theme.CARD_PADDING * 2, 12)
        pygame.draw.rect(surface, self.theme.PROGRESS_BG, bar_bg, border_radius=6)
        target = project.progress
        rendered = self.rendered_progress.get(id(project), target)
        width = int(bar_bg.width * min(1.0, rendered / 100))
        color = self.theme.PROGRESS_ACTIVE
        if project.status == "released":
            color = self.theme.PROGRESS_RELEASED
        elif project.status == "cancelled":
            color = self.theme.PROGRESS_CANCELLED
        pygame.draw.rect(surface, color, (bar_bg.x, bar_bg.y, width, bar_bg.height), border_radius=6)

        progress_label = font.render(f"{project.progress:.1f}%", True, self.theme.SUBTEXT)
        surface.blit(progress_label, (bar_bg.x, bar_bg.y - 18))

    def draw_actions_panel(self, surface: pygame.Surface, font: pygame.font.Font, title_font: pygame.font.Font) -> None:
        x = int(self.theme.WINDOW_WIDTH * 0.7)
        width = self.theme.WINDOW_WIDTH - x
        height = self.theme.WINDOW_HEIGHT - self.theme.STATUS_HEIGHT - self.theme.LOG_HEIGHT
        panel_rect = pygame.Rect(x, self.theme.STATUS_HEIGHT, width, height)
        pygame.draw.rect(surface, self.theme.PANEL, panel_rect)

        header = title_font.render("Действия", True, self.theme.TEXT)
        surface.blit(header, (panel_rect.x + self.theme.PANEL_PADDING, panel_rect.y + self.theme.PANEL_PADDING))

        self.buttons.clear()
        btn_width = width - self.theme.PANEL_PADDING * 2
        y = panel_rect.y + self.theme.PANEL_PADDING * 2 + header.get_height()

        def add_btn(label: str, cb: Callable[[], None], *, active: bool = False) -> None:
            nonlocal y
            rect = pygame.Rect(panel_rect.x + self.theme.PANEL_PADDING, y, btn_width, self.theme.BUTTON_HEIGHT)
            self.buttons.append(UIButton(rect, label, cb))
            y += self.theme.BUTTON_HEIGHT + self.theme.BUTTON_SPACING

        add_btn("Следующая неделя", self._do_next_week)
        add_btn(
            f"Авто-симуляция: {'ВКЛ' if self.auto_simulation_enabled else 'ВЫКЛ'}",
            self._toggle_auto,
        )
        add_btn("Новый проект", self._prompt_new_project)
        add_btn("Нанять сотрудника", self._prompt_hire_employee)
        add_btn("Назначить на проект", self._assign_employee_to_project)
        add_btn("Уволить сотрудника", self._fire_employee)
        add_btn("Сохранить игру", self._save_game)
        add_btn("Загрузить игру", self._load_game)
        add_btn("Выход", self._exit_ui)

        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.draw(
                surface,
                font,
                theme=self.theme,
                hovered=button.is_hovered(mouse_pos),
                active=(button.text.startswith("Авто-симуляция") and self.auto_simulation_enabled),
            )

        # Перечень проектов под кнопками
        y += self.theme.PANEL_PADDING
        header_projects = font.render("Текущие проекты", True, self.theme.TEXT)
        surface.blit(header_projects, (panel_rect.x + self.theme.PANEL_PADDING, y))
        y += header_projects.get_height() + self.theme.PANEL_PADDING
        self.project_slots.clear()
        card_height = 82
        for idx, project in enumerate(self.simulation.studio.projects):
            card_rect = pygame.Rect(panel_rect.x + self.theme.PANEL_PADDING, y, btn_width, card_height)
            self._draw_project_overview(surface, font, project, card_rect, selected=idx == self.selected_project)
            self.project_slots.append((card_rect, idx))
            y += card_height + self.theme.CARD_PADDING

        if not self.simulation.studio.projects:
            empty = font.render("Нет активных проектов", True, self.theme.SUBTEXT)
            surface.blit(empty, (panel_rect.x + self.theme.PANEL_PADDING, y))

    def draw_log_panel(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        rect = pygame.Rect(0, self.theme.WINDOW_HEIGHT - self.theme.LOG_HEIGHT, self.theme.WINDOW_WIDTH, self.theme.LOG_HEIGHT)
        pygame.draw.rect(surface, self.theme.LOG_BG, rect)
        pygame.draw.line(surface, self.theme.PANEL, (0, rect.y), (self.theme.WINDOW_WIDTH, rect.y), width=2)

        title = font.render("Лог событий", True, self.theme.TEXT)
        surface.blit(title, (self.theme.PANEL_PADDING, rect.y + self.theme.PANEL_PADDING))

        # Отображаем последние 8 сообщений
        lines = self.logs[-8:]
        y = rect.y + self.theme.PANEL_PADDING + 24
        for log in reversed(lines):  # свежие сверху
            age = log.get("age", 0.0)
            color = self.theme.TEXT if age < 3 else self.theme.SUBTEXT
            text_surf = font.render(str(log.get("text", "")), True, color)
            surface.blit(text_surf, (self.theme.PANEL_PADDING, y))
            y += font.get_linesize()

    # Обработчики --------------------------------------------------------
    def handle_mouse_click(self, pos: Tuple[int, int]) -> None:
        # Переключение вкладок "Офис / Проекты"
        for rect, mode in self.center_tabs:
            if rect.collidepoint(pos):
                self.center_mode = mode
                return

        # Клик внутри сцены офиса: выбираем сотрудника по аватару
        if self.center_mode == "office" and self.office_view.rect.collidepoint(pos):
            idx = self.office_view.handle_click(pos)
            if idx is not None:
                self.selected_employee = idx
                self.office_view.set_selected_employee(idx)
            return

        # Клик по карточке проекта в центральном режиме проектов
        if self.center_mode == "projects":
            for rect, idx in self.center_project_slots:
                if rect.collidepoint(pos):
                    self.selected_project = idx
                    return

        for rect, idx in self.employee_slots:
            if rect.collidepoint(pos):
                self.selected_employee = idx
                self.office_view.set_selected_employee(idx)
                return
        for rect, idx in self.project_slots:
            if rect.collidepoint(pos):
                self.selected_project = idx
                return
        for button in self.buttons:
            if button.is_hovered(pos):
                button.callback()
                return

    def add_log_message(self, text: str) -> None:
        self.logs.append({"text": text, "age": 0.0})
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs :]

    def _do_next_week(self) -> None:
        summary = self.simulation.get_state_summary()
        self.add_log_message(f"Началась неделя {summary['year']}-{summary['week'] + 1}")
        self.simulation.run_step()
        self.add_log_message(f"Неделя завершена. Деньги: {self.simulation.studio.cash}")

    def _toggle_auto(self) -> None:
        self.auto_simulation_enabled = not self.auto_simulation_enabled
        self.auto_timer = 0.0

    def _prompt_new_project(self) -> None:
        def submit(values: List[str]) -> None:
            title, genre, platform, complexity = values
            try:
                complexity_val = int(complexity or 10)
            except ValueError:
                complexity_val = 10
            project = GameProject(
                title=title or "Новый проект",
                genre=genre or "RPG",
                platform=platform or "PC",
                complexity=complexity_val,
            )
            self.simulation.studio.projects.append(project)
            self.add_log_message(f"Новый проект: {project.title}")

        self.dialog = ProjectDialog(submit, self.theme)

    def _prompt_hire_employee(self) -> None:
        def submit(values: List[str]) -> None:
            name, role, salary = values
            try:
                salary_val = int(salary or 10)
            except ValueError:
                salary_val = 10
            employee = Employee(
                name=name or "Новый сотрудник",
                role=role or "programmer",
                skill_code=3,
                skill_design=3,
                skill_art=3,
                skill_sound=3,
                salary=salary_val,
            )
            self.simulation.studio.employees.append(employee)
            self.add_log_message(f"Нанят сотрудник: {employee.name} ({employee.role})")

        self.dialog = EmployeeDialog(submit, self.theme)

    def _assign_employee_to_project(self) -> None:
        if self.selected_employee is None or self.selected_project is None:
            return
        if not (0 <= self.selected_employee < len(self.simulation.studio.employees)):
            return
        if not (0 <= self.selected_project < len(self.simulation.studio.projects)):
            return
        employee = self.simulation.studio.employees[self.selected_employee]
        project = self.simulation.studio.projects[self.selected_project]
        if employee not in project.assigned_employees:
            project.assigned_employees.append(employee)
            self.add_log_message(f"{employee.name} назначен на {project.title}")

    def _fire_employee(self) -> None:
        if self.selected_employee is None:
            return
        if 0 <= self.selected_employee < len(self.simulation.studio.employees):
            employee = self.simulation.studio.employees.pop(self.selected_employee)
            for project in self.simulation.studio.projects:
                if employee in project.assigned_employees:
                    project.assigned_employees.remove(employee)
            self.add_log_message(f"Уволен сотрудник: {employee.name}")
            self.selected_employee = None

    def _save_game(self) -> None:
        save_game(self.simulation)
        self.add_log_message("Игра сохранена")

    def _load_game(self) -> None:
        try:
            self.simulation = load_game()
            self.rendered_progress.clear()
            self.selected_employee = None
            self.selected_project = None
            self.office_view.simulation = self.simulation
            self.add_log_message("Сохранение загружено")
        except FileNotFoundError:
            self.add_log_message("Сохранение не найдено")

    def _exit_ui(self) -> None:
        self.running = False


__all__ = ["GamePygameUI", "UIButton", "ModalDialog", "ProjectDialog", "EmployeeDialog", "OfficeView"]
