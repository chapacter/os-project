import math
import random

import pygame

from entity.base import Healthbar
from settings import *


class Enemy(pygame.sprite.Sprite):
    def __init__(self, game, x, y, is_boss=False, is_elite=False):
        self.game = game
        self._layer = PLAYER_LAYER
        self.healthbar = Enemy_Healthbar(game, self, x, y)
        self.groups = game.all_sprites, game.enemies
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE
        self.width = TILESIZE
        self.height = TILESIZE

        self.x_change = 0
        self.y_change = 0

        self.is_boss = is_boss
        self.is_elite = is_elite

        if is_boss:
            self.health = ENEMY_HEALTH * 5
            self.ENEMY_SPEED_MOD = 0.5
        elif is_elite:
            self.health = ENEMY_HEALTH * 2
            self.ENEMY_SPEED_MOD = 0.8
        else:
            self.health = ENEMY_HEALTH
            self.ENEMY_SPEED_MOD = 1

        self.image = game.enemy_spritesheet.get_image(0, 0, self.width, self.height)
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

        self.direction = random.choice(["left", "right", "up", "down"])
        self.number_steps = random.choice([30, 40, 50, 60, 70, 80, 90])
        self.stall_steps = 120
        self.current_steps = 0

        self.state = "moving"
        self.animation_counter = 1

        self.shoot_counter = 0
        self.wait_shoot = random.choice([10, 20, 30, 40, 50, 60, 70, 80, 90])
        self.shoot_state = "halt"

    def shoot(self):
        self.shoot_counter += 1
        if self.shoot_counter >= self.wait_shoot:
            self.shoot_state = "shoot"
            self.shoot_counter = 0

    def move(self):
        if self.state == "moving":
            if self.direction == "left":
                self.x_change -= ENEMY_SPEED
                self.current_steps += 1
                if self.shoot_state == "shoot":
                    from projectiles.bullet import Enemy_Bullet

                    Enemy_Bullet(self.game, self.rect.x, self.rect.y)
                    self.shoot_state = "halt"

            elif self.direction == "right":
                self.x_change += ENEMY_SPEED
                self.current_steps += 1
                if self.shoot_state == "shoot":
                    from projectiles.bullet import Enemy_Bullet

                    Enemy_Bullet(self.game, self.rect.x, self.rect.y)
                    self.shoot_state = "halt"

            elif self.direction == "up":
                self.y_change -= ENEMY_SPEED
                self.current_steps += 1
                if self.shoot_state == "shoot":
                    from projectiles.bullet import Enemy_Bullet

                    Enemy_Bullet(self.game, self.rect.x, self.rect.y)
                    self.shoot_state = "halt"

            elif self.direction == "down":
                self.y_change += ENEMY_SPEED
                self.current_steps += 1
                if self.shoot_state == "shoot":
                    from projectiles.bullet import Enemy_Bullet

                    Enemy_Bullet(self.game, self.rect.x, self.rect.y)
                    self.shoot_state = "halt"

        elif self.state == "stalling":
            self.current_steps += 1
            if self.current_steps == self.stall_steps:
                self.state = "moving"
                self.current_steps = 0
                self.direction = random.choice(["left", "right", "up", "down"])

    def animation(self):
        down = [
            self.game.enemy_spritesheet.get_image(0, 0, self.width, self.height),
            self.game.enemy_spritesheet.get_image(32, 0, self.width, self.height),
            self.game.enemy_spritesheet.get_image(64, 0, self.width, self.height),
        ]

        left = [
            self.game.enemy_spritesheet.get_image(0, 32, self.width, self.height),
            self.game.enemy_spritesheet.get_image(32, 32, self.width, self.height),
            self.game.enemy_spritesheet.get_image(64, 32, self.width, self.height),
        ]

        right = [
            self.game.enemy_spritesheet.get_image(0, 64, self.width, self.height),
            self.game.enemy_spritesheet.get_image(32, 64, self.width, self.height),
            self.game.enemy_spritesheet.get_image(64, 64, self.width, self.height),
        ]

        up = [
            self.game.enemy_spritesheet.get_image(0, 96, self.width, self.height),
            self.game.enemy_spritesheet.get_image(32, 96, self.width, self.height),
            self.game.enemy_spritesheet.get_image(64, 96, self.width, self.height),
        ]

        if self.direction == "down":
            if self.y_change == 0:
                self.image = self.game.enemy_spritesheet.get_image(
                    0, 0, self.width, self.height
                )
            else:
                self.image = down[math.floor(self.animation_counter)]
                self.animation_counter += 0.2
                if self.animation_counter >= 3:
                    self.animation_counter = 0

        if self.direction == "up":
            if self.y_change == 0:
                self.image = self.game.enemy_spritesheet.get_image(
                    32, 96, self.width, self.height
                )
            else:
                self.image = up[math.floor(self.animation_counter)]
                self.animation_counter += 0.2
                if self.animation_counter >= 3:
                    self.animation_counter = 0

        if self.direction == "left":
            if self.x_change == 0:
                self.image = self.game.enemy_spritesheet.get_image(
                    32, 32, self.width, self.height
                )
            else:
                self.image = left[math.floor(self.animation_counter)]
                self.animation_counter += 0.2
                if self.animation_counter >= 3:
                    self.animation_counter = 0

        if self.direction == "right":
            if self.x_change == 0:
                self.image = self.game.enemy_spritesheet.get_image(
                    32, 64, self.width, self.height
                )
            else:
                self.image = right[math.floor(self.animation_counter)]
                self.animation_counter += 0.2
                if self.animation_counter >= 3:
                    self.animation_counter = 0

    def update(self):
        self.move()
        self.animation()
        self.rect.x = self.rect.x + self.x_change
        self.rect.y = self.rect.y + self.y_change
        self.x_change = 0
        self.y_change = 0
        if self.current_steps == self.number_steps:
            if self.state != "stalling":
                self.current_steps = 0
            self.number_steps = random.choice([30, 40, 50, 60, 70, 80, 90])
            self.state = "stalling"
        self.collide_block()
        self.collide_player()
        self.shoot()

    def collide_block(self):
        collide = pygame.sprite.spritecollide(self, self.game.blocks, False)
        if collide:
            if self.direction == "left":
                self.rect.x += PLAYER_SPEED
                self.direction = "right"
            elif self.direction == "right":
                self.rect.x -= PLAYER_SPEED
                self.direction = "left"
            elif self.direction == "up":
                self.rect.y += PLAYER_SPEED
                self.direction = "down"
            elif self.direction == "down":
                self.rect.y -= PLAYER_SPEED
                self.direction = "up"

    def collide_player(self):
        collide = pygame.sprite.spritecollide(self, self.game.mainPlayer, True)
        if collide:
            pass

    def damage(self, amount):
        self.health = self.health - amount
        self.healthbar.damage(ENEMY_HEALTH, self.health)

        if self.health <= 0:
            self.kill()
            self.healthbar.kill_bar()


class Enemy_Healthbar(Healthbar):
    def __init__(self, game, enemy, x, y):
        super().__init__(game, x, y, enemy)
