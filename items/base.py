import pygame

from utils.settings import *


class Item(pygame.sprite.Sprite):
    def __init__(self, game, x, y, layer, *groups):
        self.game = game
        self._layer = layer
        self.groups = groups
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE
        self.width = TILESIZE
        self.height = TILESIZE

        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
