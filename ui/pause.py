import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UILabel

from settings import WIN_WIDTH, WIN_HEIGHT


class PauseMenu:
    def __init__(self, game):
        self.game = game
        self.manager = pygame_gui.UIManager((WIN_WIDTH, WIN_HEIGHT), "ui/theme.json")
        self.is_active = False

        self.create_widgets()

    def create_widgets(self):
        center_x = WIN_WIDTH // 2
        center_y = WIN_HEIGHT // 2

        overlay_rect = pygame.Rect(0, 0, WIN_WIDTH, WIN_HEIGHT)
        self.overlay = pygame.Surface((WIN_WIDTH, WIN_HEIGHT))
        self.overlay.set_alpha(128)

        title_rect = pygame.Rect(center_x - 100, center_y - 120, 200, 50)
        self.title_label = UILabel(
            relative_rect=title_rect,
            text="PAUSED",
            manager=self.manager,
            object_id="pause_title",
        )

        button_width = 200
        button_height = 50
        button_spacing = 60

        resume_rect = pygame.Rect(
            center_x - button_width // 2, center_y - 30, button_width, button_height
        )
        self.resume_button = UIButton(
            relative_rect=resume_rect,
            text="Resume",
            manager=self.manager,
            object_id="resume_button",
        )

        save_rect = pygame.Rect(
            center_x - button_width // 2,
            center_y - 30 + button_spacing,
            button_width,
            button_height,
        )
        self.save_button = UIButton(
            relative_rect=save_rect,
            text="Save Game",
            manager=self.manager,
            object_id="save_button",
        )

        settings_rect = pygame.Rect(
            center_x - button_width // 2,
            center_y - 30 + button_spacing * 2,
            button_width,
            button_height,
        )
        self.settings_button = UIButton(
            relative_rect=settings_rect,
            text="Settings",
            manager=self.manager,
            object_id="pause_settings_button",
        )

        quit_rect = pygame.Rect(
            center_x - button_width // 2,
            center_y - 30 + button_spacing * 3,
            button_width,
            button_height,
        )
        self.quit_button = UIButton(
            relative_rect=quit_rect,
            text="Main Menu",
            manager=self.manager,
            object_id="quit_to_menu_button",
        )

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_object_id == "resume_button":
                self.hide()
                self.game.resume()
            elif event.ui_object_id == "save_button":
                self.game.save_game()
            elif event.ui_object_id == "pause_settings_button":
                self.game.open_settings()
            elif event.ui_object_id == "quit_to_menu_button":
                self.hide()
                self.game.return_to_menu()

    def update(self, time_delta):
        self.manager.update(time_delta)

    def draw(self, surface):
        surface.blit(self.overlay, (0, 0))
        self.manager.draw_ui(surface)

    def show(self):
        self.is_active = True
        self.manager.set_initial_active_element(self.resume_button)

    def hide(self):
        self.is_active = False
