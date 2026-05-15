import pygame
import pygame_gui
from pygame_gui.elements import UIButton

from ui.font_manager import font_manager
from utils.audio import audio_manager
from utils.settings import WHITE, BLACK, YELLOW


class GameOverMenu:
    def __init__(self, game):
        self.game = game
        self.manager = pygame_gui.UIManager(
            game.sc.get_size(), theme_path="ui/theme.json"
        )
        self.is_active = False

        self.overlay_alpha = 220
        self.bg_alpha = 240

        self.overlay = pygame.Surface(
            (self.game.sc.get_width(), self.game.sc.get_height())
        )
        self.overlay.set_alpha(self.overlay_alpha)

        bg_raw = pygame.image.load("assets/Death_screen.png").convert_alpha()
        img_w, img_h = bg_raw.get_size()
        screen_w = self.game.sc.get_width()
        screen_h = self.game.sc.get_height()
        scale = screen_h / img_h
        new_w = int(img_w * scale)
        bg_scaled = pygame.transform.scale(bg_raw, (new_w, screen_h))
        self.bg_x = (screen_w - new_w) // 2

        self.bg_image = pygame.Surface((new_w, screen_h), pygame.SRCALPHA)
        self.bg_image.blit(bg_scaled, (0, 0))

        self.button_width = 200
        self.button_height = 50
        self.button_spacing = 60

        self.notification = None
        self.notification_timer = 0

        self.buttons = {}
        self.create_widgets()

    def create_widgets(self):
        center_x = self.game.sc.get_width() // 2
        center_y = self.game.sc.get_height() // 2

        button_configs = [
            {"id": "menu", "text_key": "game_over.menu", "y_offset": -30},
            {"id": "quit", "text_key": "game_over.quit", "y_offset": -30 + self.button_spacing},
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
            if event.ui_object_id == "menu_button":
                self.hide()
                self.game.return_to_menu()
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
        self.overlay.set_alpha(self.overlay_alpha)
        bg = self.bg_image.copy()
        bg.fill((255, 255, 255, self.bg_alpha), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(bg, (self.bg_x, 0))
        surface.blit(self.overlay, (0, 0))

        center_x = self.game.sc.get_width() // 2
        center_y = self.game.sc.get_height() // 2

        title_surf = font_manager.render(
            font_manager.t("game_over.title"), 48, (200, 0, 0), shadow=BLACK
        )
        title_rect = title_surf.get_rect(center=(center_x, center_y - 120))
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

        if self.notification and self.notification_timer > 0:
            notif_surf = font_manager.render(self.notification, 24, YELLOW, shadow=BLACK)
            last_btn = self.buttons[list(self.buttons.keys())[-1]]
            notif_y = last_btn["rect"].y + last_btn["rect"].height + 30
            notif_rect = notif_surf.get_rect(center=(center_x, notif_y))
            surface.blit(notif_surf, notif_rect)

    def show(self):
        self.is_active = True

    def hide(self):
        self.is_active = False

    def update_texts(self):
        pass
