import random

import pygame

from utils.settings import *


class Particle(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self._layer = HEALTH_LAYER
        self.game = game
        self.groups = game.all_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.image = pygame.Surface((4, 4))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.centerx = x + random.choice([-2, -1, 0, 1, 2])
        self.rect.centery = y + 2

        self.lifetime = 4
        self.counter = 0

    def update(self):
        self.rect.y += 1
        self.counter += 1

        if self.counter == self.lifetime:
            self.counter = 0
            self.kill()


class AreaDamageParticle(pygame.sprite.Sprite):
    def __init__(self, game, x, y, damage):
        self._layer = GROUND_LAYER + 1
        self.game = game
        self.groups = game.all_sprites, game.area_particles
        pygame.sprite.Sprite.__init__(self, self.groups)
        
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 50, 50, 180), (15, 15), 15)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        
        self.hitbox = pygame.Rect(0, 0, 30, 30)
        self.hitbox.center = self.rect.center
        
        self.damage = damage
        self.lifetime = 180
        self.counter = 0

    def update(self):
        self.counter += 1
        if self.counter >= self.lifetime:
            self.kill()
            return
        
        self.hitbox.center = self.rect.center
        
        if self.game.player and self.hitbox.colliderect(self.game.player.hitbox):
            self.game.player.damage(self.damage)
