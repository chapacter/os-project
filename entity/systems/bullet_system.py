import math

import pygame

from core.ecs_world import System, World
from entity.components.bullet import BulletComponent
from entity.components.collision.block_collider import BlockColliderComponent
from entity.components.movement.velocity import VelocityComponent
from entity.components.tags import EnemyMarker
from entity.factories.effect_factory import EffectFactory
from projectiles.bullet import BOOMERANG_TURN_DISTANCE, EXPLOSION_RADIUS
from utils.settings import BULLET_SPEED


def explode_bullet(world, bc, pos_x, pos_y, all_sprites=None):
    enemies = world.query(EnemyMarker, BlockColliderComponent)
    for enemy in enemies:
        ec = world.get_component(enemy, BlockColliderComponent)
        if ec is None:
            continue
        dist = math.hypot(pos_x - ec.hitbox.centerx, pos_y - ec.hitbox.centery)
        if dist < EXPLOSION_RADIUS:
            dir = pygame.math.Vector2(
                enemy.rect.centerx - pos_x,
                enemy.rect.centery - pos_y,
            )
            if dir.length() > 0:
                dir = dir.normalize()
            enemy.take_knockback(dir, bc.knockback_force * 1.5)
            enemy.damage(bc.damage)
    EffectFactory.create_ecs_effect(
        world, pos_x, pos_y, "hit",
        groups=[all_sprites] if all_sprites else None,
    )


class BulletSystem(System):
    def __init__(self, world: World, get_player_fn=None, all_sprites=None):
        super().__init__(world)
        self._get_player = get_player_fn
        self._all_sprites = all_sprites

    def update(self, dt: float) -> None:
        for entity in self.world.query(BulletComponent, VelocityComponent):
            bc = self.world.get_component(entity, BulletComponent)
            vel = self.world.get_component(entity, VelocityComponent)
            if bc is None or vel is None:
                continue

            bc.pos_x += vel.dx
            bc.pos_y += vel.dy
            entity.rect.center = (int(bc.pos_x), int(bc.pos_y))
            bc.distance_traveled += math.hypot(vel.dx, vel.dy)

            if bc.boomerang:
                self._handle_boomerang(entity, bc, vel)

            if bc.distance_traveled >= bc.max_distance:
                if bc.explosive:
                    explode_bullet(self.world, bc, bc.pos_x, bc.pos_y, self._all_sprites)
                EffectFactory.create_ecs_effect(self.world, bc.pos_x, bc.pos_y, "hit",
                                                groups=[self._all_sprites] if self._all_sprites else None, )
                entity.kill()

    def _handle_boomerang(self, entity, bc, vel):
        player = self._get_player() if self._get_player else None
        if player is None:
            return
        if not bc.returning and bc.distance_traveled >= BOOMERANG_TURN_DISTANCE:
            bc.returning = True
        if bc.returning:
            px, py = player.rect.center
            angle = math.atan2(py - bc.pos_y, px - bc.pos_x)
            vel.dx = math.cos(angle) * BULLET_SPEED
            vel.dy = math.sin(angle) * BULLET_SPEED
            if math.hypot(bc.pos_x - px, bc.pos_y - py) < 20:
                entity.kill()
