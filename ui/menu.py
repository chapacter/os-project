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

        self.button_width = 200
        self.button_height = 50
        self.button_spacing = 70

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
                self.is_active = False
                self.game.load_game()
            elif event.ui_object_id == "settings_button":
                self.game.open_settings()
            elif event.ui_object_id == "quit_button":
                self.game.quit_game()

    def update(self, time_delta):
        self.manager.update(time_delta)

    def draw(self, surface):
        center_x = self.game.sc.get_width() // 2
        center_y = self.game.sc.get_height() // 2

        title_surf = font_manager.render("SONE TAIKO", 48, GOLD, shadow=BLACK)
        title_rect = title_surf.get_rect(center=(center_x, center_y - 150))
        surface.blit(title_surf, title_rect)

        for btn_id, btn in self.buttons.items():
            text = font_manager.t(btn["text_key"])

            text_color = YELLOW if btn.get("hovered") else WHITE
            frame_color = YELLOW if btn.get("hovered") else WHITE

            text_surf = font_manager.render(text, 24, text_color, shadow=BLACK)

            bx, by, bw, bh = btn["rect"]
            text_rect = text_surf.get_rect(center=(bx + bw // 2, by + bh // 2))
            surface.blit(text_surf, text_rect)

            pygame.draw.rect(surface, frame_color, btn["rect"], 2)

    def show(self):
        self.is_active = True

    def hide(self):
        self.is_active = False

    def update_texts(self):
        pass
