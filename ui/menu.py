import json
import os

import pygame
import pygame_gui
from pygame_gui.elements import UIButton

from ui.font_manager import font_manager
from utils.audio import audio_manager
from utils.settings import WHITE, BLACK, YELLOW

GOLD = (255, 215, 0)


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
        self.create_widgets()

    def create_widgets(self):
        center_x = self.game.sc.get_width() // 2
        center_y = self.game.sc.get_height() // 2

        button_configs = [
            {"id": "new_game", "text_key": "menu.new_game", "y_offset": -50},
            {
                "id": "continue",
                "text_key": "menu.continue",
                "y_offset": -50 + self.button_spacing,
                "can_be_disabled": True,
            },
            {
                "id": "settings",
                "text_key": "menu.settings",
                "y_offset": -50 + self.button_spacing * 2,
            },
            {
                "id": "quit",
                "text_key": "menu.quit",
                "y_offset": -50 + self.button_spacing * 3,
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
            if event.ui_object_id == "new_game_button":
                self.is_active = False
                self.game.start_new_game()
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

    def draw(self, surface):
        surface.blit(self.background, (0, 0))

        center_x = self.game.sc.get_width() // 2
        center_y = self.game.sc.get_height() // 2

        title_surf = font_manager.render("SONE TAIKO", 48, GOLD, shadow=BLACK)
        title_rect = title_surf.get_rect(center=(center_x, center_y - 150))
        surface.blit(title_surf, title_rect)

        if self.notification and self.notification_timer > 0:
            notif_surf = font_manager.render(self.notification, 24, YELLOW, shadow=BLACK)
            notif_rect = notif_surf.get_rect(center=(center_x, center_y + 220))
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
        self._update_continue_button_state()
        self.is_active = True

    def hide(self):
        self.is_active = False

    def update_texts(self):
        pass
