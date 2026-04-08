import random

import pygame

from items.base import Item
from items.loot import AnimatedLoot
from utils.audio import audio_manager
from utils.settings import GROUND_LAYER, WEAPON_TYPES, WEAPON_LAYER


class Weapon(Item):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, GROUND_LAYER, game.all_sprites, game.weapons)

        self.image = game.weapon_spritesheet.get_image(0, 0, self.width, self.height)
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

        self.animation_counter = 1

    def animate(self):
        animation = [
            self.game.weapon_spritesheet.get_image(0, 0, self.width, self.height),
            self.game.weapon_spritesheet.get_image(27, 0, self.width, self.height),
            self.game.weapon_spritesheet.get_image(55, 0, self.width, self.height),
        ]
        self.image = animation[int(self.animation_counter)]

        self.animation_counter += 0.02
        if self.animation_counter >= 3:
            self.animation_counter = 0

    def update(self):
        self.animate()


class WeaponLoot(AnimatedLoot):
    def __init__(self, game, x, y, weapon_type=None):
        self.game = game
        self._layer = WEAPON_LAYER
        self.groups = game.all_sprites, game.items
        pygame.sprite.Sprite.__init__(self, self.groups)

        if weapon_type is None:
            weapon_type = random.choice(list(WEAPON_TYPES.keys()))

        self.weapon_type = weapon_type
        self.config = WEAPON_TYPES[weapon_type]

        sprite_path = f"assets/{self.config['sheet']}"
        full_image = pygame.image.load(sprite_path).convert_alpha()
        grid_w, grid_h = self.config["grid"]
        tile_w = full_image.get_width() // grid_w
        tile_h = full_image.get_height() // grid_h

        col = self.config["col"]

        self.image = pygame.Surface((tile_w, tile_h), pygame.SRCALPHA)
        self.image.blit(full_image, (0, 0), (col * tile_w, 0, tile_w, tile_h))

        self.x = x
        self.y = y
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self._init_flight()
        self._init_animation()

    def on_pickup(self, player):
        player.sword_equipped = True
        audio_manager.play_sound("menu_select")
        self.kill()
