import pygame

from items.base import Item
from utils.settings import *


class Altar(Item):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = GROUND_LAYER + 1
        self.groups = game.all_sprites, game.decorations, game.interactables
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE
        self.width = TILESIZE
        self.height = TILESIZE

        self.used = False

        self._update_sprite()

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

    def _update_sprite(self):
        floor = getattr(self.game, "current_dungeon_floor", 1)
        theme = FLOOR_THEMES.get(floor, FLOOR_THEMES[1])
        row, col = theme["decoration"]
        src_x = col * TILESIZE
        src_y = row * TILESIZE
        self.image = self.game.terrain_spritesheet.get_image(
            src_x, src_y, self.width, self.height
        )

    def update(self):
        pass

    def interact(self):
        if self.used:
            return
        self.used = True
        player = self.game.player
        if player:
            player.health_comp.health = player.health_comp.max_health
