import math
import random

import pygame

from entity.components.bullet import BulletComponent
from entity.components.movement.velocity import VelocityComponent
from entity.components.tags import BulletMarker
from entity.ecs_helpers import ecs_register, ecs_unregister
from utils.settings import *

EXPLOSION_RADIUS = 48
BOOMERANG_TURN_DISTANCE = 250


class Bullet(pygame.sprite.Sprite):
    def __init__(
            self,
            game,
            start_x,
            start_y,
            target_x,
            target_y,
            scatter=0,
            knockback_force=None,
            piercing=False,
            explosive=False,
            boomerang=False,
    ):
        self.game = game
        self._layer = PLAYER_LAYER
        self.groups = game.all_sprites, game.bullets
        pygame.sprite.Sprite.__init__(self, self.groups)

        angle = math.atan2(target_y - start_y, target_x - start_x)
        if scatter:
            angle += random.uniform(-scatter, scatter)
        dx = math.cos(angle) * BULLET_SPEED
        dy = math.sin(angle) * BULLET_SPEED

        hit_len = math.hypot(dx, dy)
        hit_dir_x = dx / hit_len if hit_len > 0 else 1.0
        hit_dir_y = dy / hit_len if hit_len > 0 else 0.0

        self.width = TILESIZE - 2
        self.height = TILESIZE - 2

        self.image, _ = game.effects_spritesheet.get_effect("bullet", SPRITE_EFFECTS)
        self.rect = self.image.get_rect()
        self.rect.center = (start_x, start_y)

        if game.ecs_world:
            ecs_register(game.ecs_world, self, image=self.image)
            game.ecs_world.add_component(self, BulletMarker())
            game.ecs_world.add_component(
                self,
                BulletComponent(
                    damage=3,
                    knockback_force=knockback_force or BULLET_KNOCKBACK_FORCE,
                    pos_x=start_x,
                    pos_y=start_y,
                    piercing=piercing,
                    explosive=explosive,
                    boomerang=boomerang,
                    hit_dir_x=hit_dir_x,
                    hit_dir_y=hit_dir_y,
                    hits_enemies=True,
                    hits_player=False,
                ),
            )
            game.ecs_world.add_component(self, VelocityComponent(dx=dx, dy=dy))

    def kill(self):
        if self.game and self.game.ecs_world:
            ecs_unregister(self.game.ecs_world, self)
        super().kill()

    def collide_block(self):
        pass

    def collide_enemy(self):
        pass

    def update(self):
        pass


class Enemy_Bullet(pygame.sprite.Sprite):
    def __init__(self, game, start_x, start_y, target_x, target_y, scatter=0):
        self.game = game
        self._layer = ENEMY_LAYER
        self.groups = game.all_sprites, game.bullets
        pygame.sprite.Sprite.__init__(self, self.groups)

        angle = math.atan2(target_y - start_y, target_x - start_x)
        if scatter:
            angle += random.uniform(-scatter, scatter)
        dx = math.cos(angle) * BULLET_SPEED
        dy = math.sin(angle) * BULLET_SPEED

        self.width = TILESIZE
        self.height = TILESIZE

        self.image, _ = game.effects_spritesheet.get_effect("bullet", SPRITE_EFFECTS)
        tinted = self.image.copy()
        tinted.fill(pygame.Color(255, 80, 80), special_flags=pygame.BLEND_RGB_MULT)
        self.image = tinted
        self.rect = self.image.get_rect()
        self.rect.center = (start_x, start_y)

        if game.ecs_world:
            ecs_register(game.ecs_world, self, image=self.image)
            game.ecs_world.add_component(self, BulletMarker())
            game.ecs_world.add_component(
                self,
                BulletComponent(
                    damage=1,
                    knockback_force=2,
                    pos_x=start_x,
                    pos_y=start_y,
                    piercing=False,
                    explosive=False,
                    boomerang=False,
                    hit_dir_x=1,
                    hit_dir_y=0,
                    hits_enemies=False,
                    hits_player=True,
                ),
            )
            game.ecs_world.add_component(self, VelocityComponent(dx=dx, dy=dy))

    def kill(self):
        if self.game and self.game.ecs_world:
            ecs_unregister(self.game.ecs_world, self)
        super().kill()

    def collide_block(self):
        pass

    def collide_player(self):
        pass

    def update(self):
        pass
