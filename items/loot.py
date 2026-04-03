import os

import pygame

from items.base import Item
from utils.audio import audio_manager
from utils.settings import *


class LootItem(Item):
    HEAL_AMOUNT = 3

    def __init__(self, game, x, y):
        self.game = game
        self._layer = WEAPON_LAYER
        self.groups = game.all_sprites, game.items
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x
        self.y = y
        self.width = 128 // 8
        self.height = 48 // 3

        sprite_path = os.path.join("assets", "hallowicons_1.png")
        if os.path.exists(sprite_path):
            full_image = pygame.image.load(sprite_path).convert_alpha()
            tile_w = full_image.get_width() // 8
            tile_h = full_image.get_height() // 3
            row = 2
            col = 7
            src_x = col * tile_w
            src_y = row * tile_h
            self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            tile = pygame.Surface((tile_w, tile_h), pygame.SRCALPHA)
            tile.blit(full_image, (0, 0), (src_x, src_y, tile_w, tile_h))
            self.image = pygame.transform.scale(tile, (self.width, self.height))
        else:
            self.image = pygame.Surface((self.width, self.height))
            self.image.fill(GREEN)

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

        self.animation_counter = 0

    def animate(self):
        self.animation_counter += 0.05
        if self.animation_counter >= 1:
            self.animation_counter = 0

    def on_pickup(self, player):
        if hasattr(player, "health"):
            player.health = min(player.health + self.HEAL_AMOUNT, PLAYER_HEALTH)
            if hasattr(player, "healthbar"):
                player.healthbar.damage(PLAYER_HEALTH, player.health)
        audio_manager.play_sound("menu_select")
        self.kill()

    def update(self):
        collide = pygame.sprite.spritecollide(self, self.game.mainPlayer, False)
        if collide:
            self.on_pickup(collide[0])
        self.animate()
