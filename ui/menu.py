import json
import os

import pygame
import pygame_gui
from pygame_gui.elements import UIButton

from ui.font_manager import font_manager
from utils.audio import audio_manager
from utils.settings import WHITE, BLACK, YELLOW

GOLD = (255, 215, 0)
GREEN = (80, 200, 120)
BORDER_COLOR = (180, 180, 180)
PANEL_BG = (25, 25, 40)
TYPEWRITER_SPEED = 0.01


class MainMenu:
    def __init__(self, game):
        self.game = game
        self.manager = pygame_gui.UIManager(
            game.sc.get_size(), theme_path="ui/theme.json"
        )
        self.is_active = True

        self.background = pygame.image.load("assets/menu1.jpg").convert()
        self.background = pygame.transform.scale(self.background, game.sc.get_size())

        overlay = pygame.Surface(game.sc.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.background.blit(overlay, (0, 0))

        self.button_width = 200
        self.button_height = 50
        self.button_spacing = 70

        self.notification = None
        self.notification_timer = 0

        self.buttons = {}
        self.title_rect = pygame.Rect(0, 0, 400, 60)
        self.title_hovered = False
        self.story_opened = False
        self.story_fully_revealed = False
        self.story_visible = False
        self.story_chars = []
        self.story_timer = 0.0
        self.story_full_text = ""
        self.story_panel_rect = pygame.Rect(0, 0, 540, 200)
        self.create_widgets()

    def create_widgets(self):
        center_x = self.game.sc.get_width() // 2
        center_y = self.game.sc.get_height() // 2

        button_configs = [
            {"id": "standard", "text_key": "menu.standard", "y_offset": -80},
            {
                "id": "continue",
                "text_key": "menu.continue",
                "y_offset": -80 + self.button_spacing,
                "can_be_disabled": True,
            },
            {
                "id": "arena",
                "text_key": "menu.arena",
                "y_offset": -80 + self.button_spacing * 2,
            },
            {
                "id": "settings",
                "text_key": "menu.settings",
                "y_offset": -80 + self.button_spacing * 3,
            },
            {
                "id": "quit",
                "text_key": "menu.quit",
                "y_offset": -80 + self.button_spacing * 4,
            },
        ]

        for config in button_configs:
            rect = pygame.Rect(
                center_x - self.button_width // 2,
                center_y + config["y_offset"],
                self.button_width,
                self.button_height,
            )
            button = UIButton(
                relative_rect=rect,
                text="",
                manager=self.manager,
                object_id=f"{config['id']}_button",
            )
            self.buttons[config["id"]] = {
                "button": button,
                "text_key": config["text_key"],
                "rect": rect,
                "hovered": False,
            }

    def _has_save_file(self):
        if not os.path.exists("savegame.json"):
            return False
        try:
            with open("savegame.json", "r") as f:
                save_data = json.load(f)
            return save_data.get("save_valid", False)
        except Exception:
            return False

    def _update_continue_button_state(self):
        has_save = self._has_save_file()
        self.buttons["continue"]["has_save"] = has_save

    # def _render_button_text(self, button_id):
    #     btn = self.buttons[button_id]
    #     text = font_manager.t(btn["text_key"])
    #     text_surf = font_manager.render(text, 24, WHITE, shadow=BLACK)
    #
    #     tw, th = text_surf.get_size()
    #     bw, bh = btn["rect"].size
    #
    #     combined = pygame.Surface((max(tw, bw), max(th, bh)), pygame.SRCALPHA)
    #     combined.blit(text_surf, ((bw - tw) // 2, (bh - th) // 2))
    #
    #     return combined

    def handle_event(self, event):
        self.manager.process_events(event)
        if event.type == pygame.MOUSEMOTION:
            if self.title_rect.collidepoint(event.pos):
                if not self.title_hovered:
                    self.title_hovered = True
                    audio_manager.play_sound("menu_move")
            else:
                if self.title_hovered:
                    self.title_hovered = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.story_opened and self.story_panel_rect.collidepoint(event.pos):
                if not self.story_fully_revealed:
                    self.story_chars = list(self.story_full_text)
                    self.story_fully_revealed = True
                    audio_manager.play_sound("menu_select")
            elif self.title_rect.collidepoint(event.pos):
                audio_manager.play_sound("menu_select")
                self.story_opened = not self.story_opened
                if self.story_opened:
                    self.story_visible = True
                    self.story_chars = []
                    self.story_timer = 0.0
                    self.story_full_text = ""
                    self.story_fully_revealed = False
                else:
                    self.story_visible = False
                    self.story_chars = []
                    self.story_timer = 0.0
                    self.story_full_text = ""
                    self.story_fully_revealed = False
        if event.type == pygame_gui.UI_BUTTON_ON_HOVERED:
            btn_id = event.ui_object_id.replace("_button", "")
            if btn_id in self.buttons:
                self.buttons[btn_id]["hovered"] = True
            audio_manager.play_sound("menu_move")
        elif event.type == pygame_gui.UI_BUTTON_ON_UNHOVERED:
            btn_id = event.ui_object_id.replace("_button", "")
            if btn_id in self.buttons:
                self.buttons[btn_id]["hovered"] = False
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            audio_manager.play_sound("menu_select")
            if event.ui_object_id == "standard_button":
                self.is_active = False
                self.game.start_standard()
            elif event.ui_object_id == "arena_button":
                self.is_active = False
                self.game.start_arena()
            elif event.ui_object_id == "continue_button":
                if not self.buttons["continue"]["has_save"]:
                    self.show_notification("Нет доступного сохранения")
                    return
                if not self.game.load_game():
                    self.show_notification("Нет доступного сохранения")
                else:
                    self.is_active = False
            elif event.ui_object_id == "settings_button":
                self.game.open_settings()
            elif event.ui_object_id == "quit_button":
                self.game.quit_game()

    def show_notification(self, text, duration=30):
        self.notification = text
        self.notification_timer = duration

    def update(self, time_delta):
        self.manager.update(time_delta)
        if self.notification_timer > 0:
            self.notification_timer -= 1
            if self.notification_timer <= 0:
                self.notification = None
        if self.story_opened and not self.story_fully_revealed:
            full_text = font_manager.t("story.text")
            if self.story_full_text != full_text:
                self.story_full_text = full_text
                self.story_chars = []
                self.story_timer = 0.0
            if len(self.story_chars) < len(self.story_full_text):
                self.story_timer += time_delta
                chars_to_add = int(self.story_timer / TYPEWRITER_SPEED)
                if chars_to_add > 0:
                    self.story_chars.append(
                        self.story_full_text[len(self.story_chars)]
                    )
                    self.story_timer = 0.0

    def _draw_speech_bubble(self, surface, rect, bg_color, border_color, tail_size=100, border_radius=15, tail_y=None):
        if tail_y is None:
            tail_y = rect.centery - rect.y

        half_tail = 32
        top_margin = half_tail + 5
        bottom_margin = half_tail + 5
        full_w = rect.width + tail_size
        full_h = rect.height + top_margin + bottom_margin
        bubble_surf = pygame.Surface((full_w, full_h), pygame.SRCALPHA)

        main_rect = pygame.Rect(0, top_margin, rect.width, rect.height)
        pygame.draw.rect(bubble_surf, bg_color, main_rect, border_radius=border_radius)

        ty = int(tail_y) + top_margin
        tail_tip_x = rect.width + tail_size
        tail_base_x = rect.width
        tail_points = [(tail_base_x, ty - half_tail), (tail_tip_x, ty), (tail_base_x, ty + half_tail)]
        pygame.draw.polygon(bubble_surf, bg_color, tail_points)

        pygame.draw.rect(bubble_surf, border_color, main_rect, width=2, border_radius=border_radius)

        border_half_tail = half_tail + 1
        border_tail_points = [
            (tail_base_x, ty - border_half_tail),
            (tail_tip_x, ty),
            (tail_base_x, ty + border_half_tail),
        ]
        pygame.draw.polygon(bubble_surf, border_color, border_tail_points, width=2)

        surface.blit(bubble_surf, (rect.x, rect.y - top_margin))

    def draw(self, surface):
        surface.blit(self.background, (0, 0))

        center_x = self.game.sc.get_width() // 2
        center_y = self.game.sc.get_height() // 2

        title_text = "SONETAIKO"
        title_color = (255, 230, 0) if self.title_hovered else GOLD
        title_surf = font_manager.render(title_text, 48, title_color, shadow=BLACK)
        title_rect = title_surf.get_rect(center=(center_x, center_y - 150))
        surface.blit(title_surf, title_rect)

        self.title_rect = title_rect.copy()
        self.title_rect.inflate_ip(40, 20)

        if self.title_hovered:
            pygame.draw.rect(surface, GREEN, self.title_rect, 3)

            hint_text = font_manager.t("story.read_hint")
            hint_surf = font_manager.render(hint_text, 22, YELLOW, shadow=BLACK)
            hint_rect = hint_surf.get_rect(topleft=(self.title_rect.right + 10, title_rect.centery + 10))
            surface.blit(hint_surf, hint_rect)

        if self.story_opened and self.story_chars:
            story_text = "".join(self.story_chars)
            tail_size = 100
            panel_width = 515
            line_height = 22
            max_width = panel_width - 40
            words = story_text.split()
            lines = []
            current_line = ""
            for word in words:
                test_line = current_line + (" " if current_line else "") + word
                test_surf = font_manager.get_font(18).render(test_line, True, YELLOW)
                if test_surf.get_width() > max_width:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
                else:
                    current_line = test_line
            if current_line:
                lines.append(current_line)

            num_lines = len(lines)
            panel_height = max(100, num_lines * line_height + 40)
            panel_x = center_x + 140
            panel_y = center_y - 80

            hint_surf = font_manager.render(font_manager.t("story.read_hint"), 22, YELLOW, shadow=BLACK)
            hint_center_y = title_rect.centery + 10
            tail_y = hint_center_y - panel_y
            tail_y = max(45, min(panel_height - 45, tail_y))

            panel_rect_content = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
            self.story_panel_rect = pygame.Rect(panel_x, panel_y, panel_width + tail_size, panel_height)

            self._draw_speech_bubble(surface, panel_rect_content, PANEL_BG, BORDER_COLOR, tail_size=tail_size, border_radius=15, tail_y=tail_y)

            for i, line in enumerate(lines):
                line_surf = font_manager.render(line, 18, YELLOW, shadow=BLACK)
                line_rect = line_surf.get_rect(topleft=(panel_x + 20, panel_y + 20 + i * line_height))
                surface.blit(line_surf, line_rect)

        if self.notification and self.notification_timer > 0:
            notif_surf = font_manager.render(self.notification, 24, YELLOW, shadow=BLACK)
            notif_rect = notif_surf.get_rect(center=(center_x, center_y + 270))
            surface.blit(notif_surf, notif_rect)

        for btn_id, btn in self.buttons.items():
            text = font_manager.t(btn["text_key"])

            is_disabled = btn_id == "continue" and not btn.get("has_save", False)

            if is_disabled:
                text_color = (100, 100, 100)
                frame_color = (100, 100, 100)
            else:
                text_color = YELLOW if btn.get("hovered") else WHITE
                frame_color = YELLOW if btn.get("hovered") else WHITE

            text_surf = font_manager.render(text, 24, text_color, shadow=BLACK)

            bx, by, bw, bh = btn["rect"]
            text_rect = text_surf.get_rect(center=(bx + bw // 2, by + bh // 2))
            surface.blit(text_surf, text_rect)

            pygame.draw.rect(surface, frame_color, btn["rect"], 2)

    def show(self):
        self.reset_story()
        self._update_continue_button_state()
        self.is_active = True

    def reset_story(self):
        self.story_opened = False
        self.story_fully_revealed = False
        self.story_visible = False
        self.story_chars = []
        self.story_timer = 0.0
        self.story_full_text = ""
        self.title_hovered = False

    def hide(self):
        self.is_active = False

    def update_texts(self):
        self.story_chars = []
        self.story_timer = 0.0
        self.story_full_text = ""
        self.story_fully_revealed = False
        if self.story_opened:
            self.story_opened = False
            self.story_visible = False
