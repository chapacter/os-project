import os

import pygame

from items.loot import LootItem
from utils.audio import audio_manager
from utils.settings import *


class Berry(LootItem):
    HEAL_AMOUNT = 6

    def __init__(self, game, x, y):
        super().__init__(game, x, y)

        sprite_path = os.path.join("assets", "berry.png")
        if os.path.exists(sprite_path):
            self.image = pygame.image.load(sprite_path).convert_alpha()
        else:
            self.image = pygame.Surface((self.width, self.height))
            self.image.fill(RED)

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
