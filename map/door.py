import pygame

from utils.settings import *


class Door(pygame.sprite.Sprite):
    def __init__(self, game, x, y, direction, from_room_coord, to_room_coord):
        self.game = game
        self._layer = GROUND_LAYER
        self.groups = game.all_sprites, game.doors
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE
        self.width = TILESIZE * 2  # Door width is 2 tiles
        self.height = TILESIZE * 2

        self.direction = direction
        self.from_room_coord = from_room_coord
        self.to_room_coord = to_room_coord

        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y
