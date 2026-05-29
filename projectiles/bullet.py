import math
import random

import pygame

from entity.factories.effect_factory import EffectFactory
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

        self.start_x = start_x
        self.start_y = start_y

        angle = math.atan2(target_y - start_y, target_x - start_x)
        if scatter:
            angle += random.uniform(-scatter, scatter)
        self.dx = math.cos(angle) * BULLET_SPEED
        self.dy = math.sin(angle) * BULLET_SPEED

        self.hit_dir = pygame.math.Vector2(self.dx, self.dy)
        if self.hit_dir.length() > 0:
            self.hit_dir = self.hit_dir.normalize()
        self.knockback_force = knockback_force or BULLET_KNOCKBACK_FORCE

        self.x = start_x
        self.y = start_y
        self.distance_traveled = 0

        self.width = TILESIZE - 2
        self.height = TILESIZE - 2

        self.image, _ = game.effects_spritesheet.get_effect("bullet", SPRITE_EFFECTS)
        self.rect = self.image.get_rect()
        self.rect.center = (start_x, start_y)

        self.damage = 3

        self.piercing = piercing
        self.explosive = explosive
        self.boomerang = boomerang
        self._hit_enemies = []
        self._returning = False

    def move(self):
        self.x += self.dx
        self.y += self.dy
        self.rect.center = (self.x, self.y)
        self.distance_traveled += BULLET_SPEED

        if self.boomerang:
            if not self._returning and self.distance_traveled >= BOOMERANG_TURN_DISTANCE:
                self._returning = True
            if self._returning:
                px, py = self.game.player.rect.center
                angle = math.atan2(py - self.y, px - self.x)
                self.dx = math.cos(angle) * BULLET_SPEED
                self.dy = math.sin(angle) * BULLET_SPEED
                if math.hypot(self.x - px, self.y - py) < 20:
                    self.kill()
                    return

        if self.distance_traveled >= BULLET_MAX_DISTANCE:
            if self.explosive:
                self.explode()
            else:
                self.kill()

    def collide_block(self):
        collide = pygame.sprite.spritecollide(self, self.game.blocks, False)
        if collide:
            if self.explosive:
                self.explode()
            else:
                self.kill()

    def collide_enemy(self):
        for enemy in self.game.enemies:
            if self.rect.colliderect(enemy.hitbox) and enemy not in self._hit_enemies:
                self._hit_enemies.append(enemy)

                knockback_dir = pygame.math.Vector2(
                    enemy.rect.centerx - self.rect.centerx,
                    enemy.rect.centery - self.rect.centery,
                )
                if knockback_dir.length() > 0:
                    knockback_dir = knockback_dir.normalize()
                else:
                    knockback_dir = self.hit_dir.copy()

                EffectFactory.create_ecs_effect(self.game.ecs_world, self.rect.centerx, self.rect.centery, "hit",
                                                groups=[self.game.all_sprites])
                enemy.take_knockback(knockback_dir, self.knockback_force)
                enemy.damage(self.damage)

                if self.explosive:
                    self.explode(kill=not self.piercing)
                    if not self.piercing:
                        return
                elif not self.piercing:
                    self.kill()
                    return

    def explode(self, kill=True):
        for enemy in self.game.enemies:
            dist = math.hypot(
                self.rect.centerx - enemy.rect.centerx,
                self.rect.centery - enemy.rect.centery,
            )
            if dist < EXPLOSION_RADIUS:
                dir = pygame.math.Vector2(
                    enemy.rect.centerx - self.rect.centerx,
                    enemy.rect.centery - self.rect.centery,
                )
                if dir.length() > 0:
                    dir = dir.normalize()
                enemy.take_knockback(dir, self.knockback_force * 1.5)
                enemy.damage(self.damage)
        EffectFactory.create_ecs_effect(self.game.ecs_world, self.rect.centerx, self.rect.centery, "hit",
                                        groups=[self.game.all_sprites])
        if kill:
            self.kill()

    def update(self):
        self.move()
        self.collide_enemy()
        self.collide_block()


class Enemy_Bullet(pygame.sprite.Sprite):
    def __init__(self, game, start_x, start_y, target_x, target_y, scatter=0):
        self.game = game
        self._layer = ENEMY_LAYER
        self.groups = game.all_sprites, game.bullets
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.start_x = start_x
        self.start_y = start_y

        angle = math.atan2(target_y - start_y, target_x - start_x)
        if scatter:
            angle += random.uniform(-scatter, scatter)
        self.dx = math.cos(angle) * BULLET_SPEED
        self.dy = math.sin(angle) * BULLET_SPEED

        self.x = start_x
        self.y = start_y
        self.distance_traveled = 0

        self.width = TILESIZE
        self.height = TILESIZE

        self.image, _ = game.effects_spritesheet.get_effect("bullet", SPRITE_EFFECTS)
        tinted = self.image.copy()
        tinted.fill(pygame.Color(255, 80, 80), special_flags=pygame.BLEND_RGB_MULT)
        self.image = tinted
        self.rect = self.image.get_rect()
        self.rect.center = (start_x, start_y)

        self.damage = 1

    def move(self):
        self.x += self.dx
        self.y += self.dy
        self.rect.center = (self.x, self.y)
        self.distance_traveled += BULLET_SPEED
        if self.distance_traveled >= BULLET_MAX_DISTANCE:
            self.kill()

    def collide_block(self):
        collide = pygame.sprite.spritecollide(self, self.game.blocks, False)
        if collide:
            self.kill()

    def collide_player(self):
        for player in self.game.mainPlayer:
            if self.rect.colliderect(player.hitbox):
                EffectFactory.create_ecs_effect(self.game.ecs_world, self.rect.centerx, self.rect.centery, "hit",
                                                groups=[self.game.all_sprites], )
                player.damage(self.damage)
                self.kill()
                break

    def update(self):
        self.move()
        self.collide_player()
        self.collide_block()
