import pygame
import pygame_gui
from pygame_gui.elements import UILabel

from settings import WIN_WIDTH, WIN_HEIGHT


class HUD:
    def __init__(self, game):
        self.game = game
        self.manager = pygame_gui.UIManager((WIN_WIDTH, WIN_HEIGHT), "ui/theme.json")
        self.is_active = True
        self.font = pygame.font.Font(None, 24)

        self.create_widgets()

    def create_widgets(self):
        health_bar_width = 200
        health_bar_height = 20

        self.health_label = UILabel(
            relative_rect=pygame.Rect(20, 20, 100, 30),
            text="Health:",
            manager=self.manager,
            object_id="health_label",
        )

        self.health_bar_bg = pygame.Surface((health_bar_width, health_bar_height))
        self.health_bar_bg.fill((50, 50, 50))

        self.health_bar = pygame.Surface((health_bar_width - 4, health_bar_height - 4))
        self.health_bar.fill((255, 0, 0))

        self.enemy_count_label = UILabel(
            relative_rect=pygame.Rect(20, 60, 150, 30),
            text="Enemies: 0",
            manager=self.manager,
            object_id="enemy_count",
        )

        self.floor_label = UILabel(
            relative_rect=pygame.Rect(20, 100, 150, 30),
            text="Floor: 1",
            manager=self.manager,
            object_id="floor_label",
        )

        self.zone_label = UILabel(
            relative_rect=pygame.Rect(20, 140, 200, 30),
            text="Zone: (0, 0)",
            manager=self.manager,
            object_id="zone_label",
        )

    def update(self, time_delta):
        self.manager.update(time_delta)

        if hasattr(self.game, "player") and self.game.player:
            health = self.game.player.health
            max_health = 10
            health_percent = max(0, min(1, health / max_health))

            self.health_bar = pygame.Surface((int((196) * health_percent), 16))
            if health_percent > 0.5:
                self.health_bar.fill((0, 255, 0))
            elif health_percent > 0.25:
                self.health_bar.fill((255, 255, 0))
            else:
                self.health_bar.fill((255, 0, 0))

        if hasattr(self.game, "enemies"):
            enemy_count = len(self.game.enemies)
            self.enemy_count_label.set_text(f"Enemies: {enemy_count}")

        if hasattr(self.game, "current_dungeon_floor"):
            floor = self.game.current_dungeon_floor
            self.floor_label.set_text(f"Floor: {floor}")

        if hasattr(self.game, "current_zone"):
            zone = self.game.current_zone
            self.zone_label.set_text(f"Zone: {zone}")

    def draw(self, surface):
        self.manager.draw_ui(surface)

        surface.blit(self.health_bar_bg, (80, 22))
        surface.blit(self.health_bar, (82, 24))

    def show(self):
        self.is_active = True

    def hide(self):
        self.is_active = False
