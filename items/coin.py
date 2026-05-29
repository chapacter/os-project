import os
import random

import pygame

from items.loot import AnimatedLoot
from utils.audio import audio_manager
from utils.settings import WEAPON_LAYER


COIN_CONFIG = {
    "bronze": {"file": "assets/bronze_coin.png", "value": 1},
    "silver": {"file": "assets/silver_coin.png", "value": 3},
    "gold": {"file": "assets/gold_coin.png", "value": 5},
}


class Coin(AnimatedLoot):
    def __init__(self, game, x, y, coin_type="bronze"):
        self.game = game
        self._layer = WEAPON_LAYER
        self.groups = game.all_sprites, game.items
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.coin_type = coin_type
        self.value = COIN_CONFIG[coin_type]["value"]

        path = COIN_CONFIG[coin_type]["file"]
        img = pygame.image.load(path).convert_alpha()
        self.image = img

        self.x = x
        self.y = y
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self._init_flight()
        self._init_animation()

    def on_pickup(self, player):
        if hasattr(player, "coins"):
            player.coins += self.value
        audio_manager.play_sound("menu_select")
        self.kill()
