import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UILabel

from utils.audio import audio_manager


class MainMenu:
    def __init__(self, game):
        self.game = game
        self.manager = pygame_gui.UIManager(game.sc.get_size(), "ui/theme.json")
        self.is_active = True

        self.create_widgets()

    def create_widgets(self):
        center_x = self.game.sc.get_width() // 2
        center_y = self.game.sc.get_height() // 2

        title_rect = pygame.Rect(center_x - 150, center_y - 150, 300, 60)
        self.title_label = UILabel(
            relative_rect=title_rect,
            text="SONE TAIKO",
            manager=self.manager,
            object_id="title",
        )

        button_width = 200
        button_height = 50
        button_spacing = 70

        new_game_rect = pygame.Rect(
            center_x - button_width // 2, center_y - 50, button_width, button_height
        )
        self.new_game_button = UIButton(
            relative_rect=new_game_rect,
            text="New Game",
            manager=self.manager,
            object_id="new_game_button",
        )

        continue_rect = pygame.Rect(
            center_x - button_width // 2,
            center_y - 50 + button_spacing,
            button_width,
            button_height,
        )
        self.continue_button = UIButton(
            relative_rect=continue_rect,
            text="Continue",
            manager=self.manager,
            object_id="continue_button",
        )

        settings_rect = pygame.Rect(
            center_x - button_width // 2,
            center_y - 50 + button_spacing * 2,
            button_width,
            button_height,
        )
        self.settings_button = UIButton(
            relative_rect=settings_rect,
            text="Settings",
            manager=self.manager,
            object_id="settings_button",
        )

        quit_rect = pygame.Rect(
            center_x - button_width // 2,
            center_y - 50 + button_spacing * 3,
            button_width,
            button_height,
        )
        self.quit_button = UIButton(
            relative_rect=quit_rect,
            text="Quit",
            manager=self.manager,
            object_id="quit_button",
        )

    def handle_event(self, event):
        self.manager.process_events(event)
        if event.type == pygame_gui.UI_BUTTON_ON_HOVERED:
            audio_manager.play_sound("menu_move")
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
        self.manager.draw_ui(surface)

    def show(self):
        self.is_active = True

    def hide(self):
        self.is_active = False
