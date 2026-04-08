import pygame

from items.base import Item
from items.food import Food
from items.weapon import WeaponLoot
from utils.settings import *


class Chest(Item):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = GROUND_LAYER
        self.groups = game.all_sprites, game.chests, game.interactables
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE
        self.width = TILESIZE
        self.height = TILESIZE

        self.opened = False

        self._update_sprite()

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

    def _update_sprite(self):
        floor = getattr(self.game, "current_dungeon_floor", 1)
        theme = FLOOR_THEMES.get(floor, FLOOR_THEMES[1])
        key = "chest_open" if self.opened else "chest_closed"
        row, col = theme[key]
        src_x = col * TILESIZE
        src_y = row * TILESIZE
        self.image = self.game.terrain_spritesheet.get_image(
            src_x, src_y, self.width, self.height
        )

    def update(self):
        pass

    def interact(self):
        if not self.opened:
            self.open()

    def open(self):
        self.opened = True
        self._update_sprite()

        WeaponLoot(self.game, self.x, self.y)

        for _ in range(2):
            Food(self.game, self.x, self.y)
