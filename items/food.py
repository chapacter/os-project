import random

import pygame

from items.loot import AnimatedLoot
from utils.audio import audio_manager
from utils.settings import FOOD_TYPES, WEAPON_LAYER, PLAYER_HEALTH


class Food(AnimatedLoot):
    def __init__(self, game, x, y, food_type=None):
        self.game = game
        self._layer = WEAPON_LAYER
        self.groups = game.all_sprites, game.items
        pygame.sprite.Sprite.__init__(self, self.groups)

        if food_type is None:
            food_type = random.choice(list(FOOD_TYPES.keys()))

        self.food_type = food_type
        self.config = FOOD_TYPES[food_type]
        self.HEAL_AMOUNT = self.config["heal"]

        sprite_path = f"assets/{self.config['sheet']}"
        full_image = pygame.image.load(sprite_path).convert_alpha()
        grid_w, grid_h = self.config["grid"]
        tile_w = full_image.get_width() // grid_w
        tile_h = full_image.get_height() // grid_h

        row = self.config["row"]
        col = random.randint(0, grid_w - 1)

        self.image = pygame.Surface((tile_w, tile_h), pygame.SRCALPHA)
        self.image.blit(
            full_image, (0, 0), (col * tile_w, row * tile_h, tile_w, tile_h)
        )

        self.x = x
        self.y = y
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self._init_flight()
        self._init_animation()

    def on_pickup(self, player):
        if hasattr(player, "health"):
            player.health = min(player.health + self.HEAL_AMOUNT, PLAYER_HEALTH)
            if hasattr(player, "healthbar"):
                player.healthbar.damage(PLAYER_HEALTH, player.health)
        audio_manager.play_sound("menu_select")
        self.kill()
