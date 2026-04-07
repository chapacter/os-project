import os
import random

import pygame

from items.base import Item
from utils.audio import audio_manager
from utils.settings import *


class LootItem(Item):
    HEAL_AMOUNT = 3
    FLY_DURATION = 30

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

        self.state = "flying"
        self.fly_timer = 0

        self.start_pos = pygame.math.Vector2(self.rect.x, self.rect.y)
        distance = random.randint(20, 50)
        direction = random.choice([(-1, 1), (1, 1), (1, -1), (-1, -1)])
        offset_x = direction[0] * distance
        offset_y = direction[1] * distance
        self.end_pos = pygame.math.Vector2(
            self.start_pos.x + offset_x, self.start_pos.y + offset_y
        )
        mid_x = (self.start_pos.x + self.end_pos.x) / 2
        mid_y = (self.start_pos.y + self.end_pos.y) / 2
        self.apex_pos = pygame.math.Vector2(mid_x, mid_y - 10)

    def _get_parabola_pos(self, t):
        one_minus_t = 1 - t
        return (
                one_minus_t * one_minus_t * self.start_pos
                + 2 * one_minus_t * t * self.apex_pos
                + t * t * self.end_pos
        )

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
        if self.state == "flying":
            self.fly_timer += 1
            t = self.fly_timer / self.FLY_DURATION
            pos = self._get_parabola_pos(t)
            self.rect.x = pos.x
            self.rect.y = pos.y

            if self.fly_timer >= self.FLY_DURATION:
                self.state = "landed"
                self.rect.x = self.end_pos.x
                self.rect.y = self.end_pos.y
        else:
            collide = pygame.sprite.spritecollide(self, self.game.mainPlayer, False)
            if collide:
                self.on_pickup(collide[0])

        self.animate()
