import os

import pygame

from items.base import Item
from utils.settings import *


class Berry(Item):
    HEAL_AMOUNT = 3

    def __init__(self, game, x, y):
        super().__init__(game, x, y, GROUND_LAYER, game.all_sprites, game.items)

        sprite_path = os.path.join('simple', 'assets', 'berry.png')
        if os.path.exists(sprite_path):
            self.image = pygame.image.load(sprite_path).convert()
            self.image.set_colorkey((0, 0, 0))
        else:
            self.image = pygame.Surface((self.width, self.height))
            self.image.fill(RED)

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

        self.animation_counter = 0

    def animate(self):
        self.animation_counter += 0.05
        if self.animation_counter >= 1:
            self.animation_counter = 0

    def on_pickup(self, player):
        if hasattr(player, 'health'):
            player.health = min(player.health + self.HEAL_AMOUNT, PLAYER_HEALTH)
            if hasattr(player, 'healthbar'):
                player.healthbar.damage(PLAYER_HEALTH, player.health)
        self.kill()

    def update(self):
        collide = pygame.sprite.spritecollide(self, self.game.mainPlayer, False)
        if collide:
            self.on_pickup(collide[0])
        self.animate()
