import os
import random

import pygame

from items.loot import LootItem
from utils.audio import audio_manager
from utils.settings import *


class Food(LootItem):
    HEAL_AMOUNT = 3

    def __init__(self, game, x, y):
        super().__init__(game, x, y)

        sprite_path = os.path.join("assets", "hallowicons_1.png")
        if os.path.exists(sprite_path):
            full_image = pygame.image.load(sprite_path).convert_alpha()
            tile_w = full_image.get_width() // 8
            tile_h = full_image.get_height() // 3

            row = random.randint(0, 2)
            col = random.randint(0, 7)
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

    def on_pickup(self, player):
        if hasattr(player, "health"):
            player.health = min(player.health + self.HEAL_AMOUNT, PLAYER_HEALTH)
            if hasattr(player, "healthbar"):
                player.healthbar.damage(PLAYER_HEALTH, player.health)
        audio_manager.play_sound("menu_select")
        self.kill()
