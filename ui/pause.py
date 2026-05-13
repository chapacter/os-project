import pygame
import pygame_gui
from pygame_gui.elements import UIButton

from ui.font_manager import font_manager
from utils.audio import audio_manager
from utils.settings import WHITE, BLACK, YELLOW, WORLD_ZONE_WIDTH, WORLD_ZONE_HEIGHT


class PauseMenu:
    def __init__(self, game):
        self.game = game
        self.manager = pygame_gui.UIManager(
            game.sc.get_size(), theme_path="ui/theme.json"
        )
        self.is_active = False

        self.overlay = pygame.Surface(
            (self.game.sc.get_width(), self.game.sc.get_height())
        )
        self.overlay.set_alpha(128)

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
            {"id": "resume", "text_key": "pause.resume", "y_offset": -30},
            {
                "id": "save",
                "text_key": "pause.save",
                "y_offset": -30 + self.button_spacing,
            },
            {
                "id": "settings",
                "text_key": "menu.settings",
                "y_offset": -30 + self.button_spacing * 2,
            },
            {
                "id": "main_menu",
                "text_key": "pause.return_to_menu",
                "y_offset": -30 + self.button_spacing * 3,
            },
            {
                "id": "quit",
                "text_key": "pause.quit_to_desktop",
                "y_offset": -30 + self.button_spacing * 4,
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
            if event.ui_object_id == "resume_button":
                self.hide()
                self.game.resume()
            elif event.ui_object_id == "save_button":
                self.game.save_game()
                self.show_notification("Игра сохранена")
            elif event.ui_object_id == "settings_button":
                self.game.open_settings()
            elif event.ui_object_id == "main_menu_button":
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
        surface.blit(self.overlay, (0, 0))

        TILESIZE = 32

        seed_text = "World Seed: --"
        if hasattr(self.game, "world_seed") and self.game.world_seed is not None:
            seed_text = f"World Seed: {self.game.world_seed}"
        seed_surf = font_manager.render(seed_text, 18, WHITE)
        surface.blit(seed_surf, (20, 20))

        coord_text = "Coords: --"
        zone_text = "Zone: --"
        if hasattr(self.game, "player") and self.game.player:
            px = int(self.game.player.rect.x // TILESIZE)
            py = int(self.game.player.rect.y // TILESIZE)
            coord_text = f"Coords: {px}, {py}"

            if self.game.mode == "world":
                zone_x = px // WORLD_ZONE_WIDTH
                zone_y = py // WORLD_ZONE_HEIGHT
                zone_text = f"Zone: ({zone_x}, {zone_y})"
            elif self.game.mode == "dungeon":
                room = self.game.dungeon_generator.get_room_at(px, py)
                zone_text = f"Room: {room}"

        coord_surf = font_manager.render(coord_text, 18, WHITE)
        surface.blit(coord_surf, (20, 50))

        if hasattr(self.game, "enemies"):
            enemy_count = len(self.game.enemies)
            enemies_text = f"Enemies: {enemy_count}"
            enemies_surf = font_manager.render(enemies_text, 18, WHITE)
            surface.blit(enemies_surf, (20, 80))

        floor = getattr(self.game, "current_dungeon_floor", None)
        if floor is not None:
            floor_text = f"Floor: {floor}"
            floor_surf = font_manager.render(floor_text, 18, WHITE)
            surface.blit(floor_surf, (20, 110))

        zone_surf = font_manager.render(zone_text, 18, WHITE)
        surface.blit(zone_surf, (20, 140))

        center_x = self.game.sc.get_width() // 2
        center_y = self.game.sc.get_height() // 2

        title_surf = font_manager.render(
            font_manager.t("pause.title"), 48, WHITE, shadow=BLACK
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
