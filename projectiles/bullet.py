import math
import random

import pygame

from effects.effect import Effect
from utils.settings import *


class Bullet(pygame.sprite.Sprite):
    def __init__(self, game, start_x, start_y, target_x, target_y, scatter=0):
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

        self.x = start_x
        self.y = start_y
        self.distance_traveled = 0

        self.width = TILESIZE - 2
        self.height = TILESIZE - 2

        self.image, _ = game.effects_spritesheet.get_effect("bullet", SPRITE_EFFECTS)
        self.rect = self.image.get_rect()
        self.rect.center = (start_x, start_y)

        self.damage = 3

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

    def collide_enemy(self):
        collide = pygame.sprite.spritecollide(self, self.game.enemies, False)
        if collide:
            Effect(self.game, self.rect.centerx, self.rect.centery, "hit")
            collide[0].damage(self.damage)
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
                Effect(self.game, self.rect.centerx, self.rect.centery, "hit")
                player.damage(self.damage)
                self.kill()
                break

    def update(self):
        self.move()
        self.collide_player()
        self.collide_block()
