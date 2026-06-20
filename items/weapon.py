import random

import pygame

from entity.components.render.animation import AnimationComponent
from entity.components.tags import WeaponMarker
from entity.ecs_helpers import ecs_register
from items.base import Item
from items.loot import AnimatedLoot
from utils.settings import GROUND_LAYER, WEAPON_TYPES, WEAPON_LAYER


class Weapon(Item):
    def __init__(self, game, x, y):
        super().__init__(game, x, y, GROUND_LAYER, game.all_sprites, game.weapons)

        frames = [
            game.weapon_spritesheet.get_image(0, 0, self.width, self.height),
            game.weapon_spritesheet.get_image(27, 0, self.width, self.height),
            game.weapon_spritesheet.get_image(55, 0, self.width, self.height),
        ]
        self.image = frames[1]

        self.anim_comp = AnimationComponent(
            frames=frames, frame_count=3, speed=0.02, looping=True,
        )

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

        if game.ecs_world:
            game.ecs_world.add_component(self, self.anim_comp)
            ecs_register(game.ecs_world, self, rect=self.rect, image=self.image)
            game.ecs_world.add_component(self, WeaponMarker())


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
        self._register_ecs()

    _FLAG_MAP = {
        "double_weapon": "double_attack_unlocked",
        "cone_weapon": "cone_attack_unlocked",
        "pierce_weapon": "pierce_unlocked",
        "explode_weapon": "explode_unlocked",
        "boomerang_weapon": "boomerang_unlocked",
    }

    def on_pickup(self, player):
        player.sword_equipped = True
        name = self.config["name"]
        flag = self._FLAG_MAP.get(name)
        if flag:
            setattr(player, flag, True)
            setattr(player.game, flag, True)
        self.game.services.audio.play_sound("menu_select")
        self.kill()
