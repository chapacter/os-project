import random

import pygame

from settings import *


class Particle(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self._layer = HEALTH_LAYER
        self.game = game
        self.groups = game.all_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.image = pygame.Surface((4, 4))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = x + random.choice([-1, 0, 1, 5, 10, 15])
        self.rect.y = y + TILESIZE

        self.lifetime = 4
        self.counter = 0

    def update(self):
        self.rect.y += 1
        self.counter += 1

        if self.counter == self.lifetime:
            self.counter = 0
            self.kill()
