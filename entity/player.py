import math

import pygame

from entity.base import Healthbar
from settings import *


class Player(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = PLAYER_LAYER
        self.healthbar = Player_Healthbar(game, self, x, y)

        self.groups = game.all_sprites, game.mainPlayer
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE
        self.width = TILESIZE
        self.height = TILESIZE

        self.x_change = 0
        self.y_change = 0
        self.animationCounter = 1

        self.image = game.player_spritesheet.get_image(52, 0, self.width, self.height)
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

        self.direction = "right"
        self.sword_equipped = False

        self.counter = 0
        self.wait_time = 10
        self.shoot_state = "shoot"

        self.health = PLAYER_HEALTH

    def move(self):
        from effects.particle import Particle
        Particle(self.game, self.rect.x, self.rect.y)

        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_a]:
            self.x_change -= PLAYER_SPEED
            self.direction = "left"
        elif pressed[pygame.K_d]:
            self.x_change += PLAYER_SPEED
            self.direction = "right"
        if pressed[pygame.K_w]:
            self.y_change -= PLAYER_SPEED
            self.direction = "up"
        elif pressed[pygame.K_s]:
            self.y_change += PLAYER_SPEED
            self.direction = "down"

    def update(self):
        self.move()
        self.animation()
        self.rect.x = self.rect.x + self.x_change
        self.rect.y = self.rect.y + self.y_change
        self.collide_block()
        self.collide_enemy()
        self.collide_weapon()
        self.shoot_sword()
        self.wait_after_shoot()
        self.x_change = 0
        self.y_change = 0

    def animation(self):
        down = [self.game.player_spritesheet.get_image(0, 52, self.width, self.height),
                self.game.player_spritesheet.get_image(26, 52, self.width, self.height),
                self.game.player_spritesheet.get_image(52, 52, self.width, self.height),
                self.game.player_spritesheet.get_image(78, 52, self.width, self.height),
                self.game.player_spritesheet.get_image(104, 52, self.width, self.height),
                self.game.player_spritesheet.get_image(130, 52, self.width, self.height)]

        left = [self.game.player_spritesheet.get_image(0, 78, self.width, self.height),
                self.game.player_spritesheet.get_image(26, 78, self.width, self.height),
                self.game.player_spritesheet.get_image(52, 78, self.width, self.height),
                self.game.player_spritesheet.get_image(78, 78, self.width, self.height),
                self.game.player_spritesheet.get_image(104, 78, self.width, self.height),
                self.game.player_spritesheet.get_image(130, 78, self.width, self.height)]

        right = [self.game.player_spritesheet.get_image(0, 0, self.width, self.height),
                 self.game.player_spritesheet.get_image(26, 0, self.width, self.height),
                 self.game.player_spritesheet.get_image(52, 0, self.width, self.height),
                 self.game.player_spritesheet.get_image(78, 0, self.width, self.height),
                 self.game.player_spritesheet.get_image(104, 0, self.width, self.height),
                 self.game.player_spritesheet.get_image(130, 0, self.width, self.height)]

        up = [self.game.player_spritesheet.get_image(0, 26, self.width, self.height),
              self.game.player_spritesheet.get_image(26, 26, self.width, self.height),
              self.game.player_spritesheet.get_image(52, 26, self.width, self.height),
              self.game.player_spritesheet.get_image(78, 26, self.width, self.height),
              self.game.player_spritesheet.get_image(104, 26, self.width, self.height),
              self.game.player_spritesheet.get_image(130, 26, self.width, self.height)]

        if self.direction == "down":
            if self.y_change == 0:
                self.image = self.game.player_spritesheet.get_image(0, 52, self.width, self.height)
            else:
                self.image = down[math.floor(self.animationCounter)]
                self.animationCounter += 0.2
                if self.animationCounter >= 6:
                    self.animationCounter = 0

        if self.direction == "up":
            if self.y_change == 0:
                self.image = self.game.player_spritesheet.get_image(1, 27, self.width, self.height)
            else:
                self.image = up[math.floor(self.animationCounter)]
                self.animationCounter += 0.2
                if self.animationCounter >= 3:
                    self.animationCounter = 0

        if self.direction == "left":
            if self.x_change == 0:
                self.image = self.game.player_spritesheet.get_image(1, 79, self.width, self.height)
            else:
                self.image = left[math.floor(self.animationCounter)]
                self.animationCounter += 0.2
                if self.animationCounter >= 3:
                    self.animationCounter = 0

        if self.direction == "right":
            if self.x_change == 0:
                self.image = self.game.player_spritesheet.get_image(1, 1, self.width, self.height)
            else:
                self.image = right[math.floor(self.animationCounter)]
                self.animationCounter += 0.2
                if self.animationCounter >= 3:
                    self.animationCounter = 0

    def collide_block(self):
        pressed = pygame.key.get_pressed()
        collide = pygame.sprite.spritecollide(self, self.game.blocks, False, pygame.sprite.collide_rect_ratio(0.85))

        if collide:
            self.game.block_collided = True
            if pressed[pygame.K_a]:
                self.rect.x += PLAYER_SPEED
            elif pressed[pygame.K_d]:
                self.rect.x -= PLAYER_SPEED
            if pressed[pygame.K_w]:
                self.rect.y += PLAYER_SPEED
            elif pressed[pygame.K_s]:
                self.rect.y -= PLAYER_SPEED
        else:
            self.game.block_collided = False

    def collide_enemy(self):
        pressed = pygame.key.get_pressed()
        collide = pygame.sprite.spritecollide(self, self.game.enemies, False, pygame.sprite.collide_rect_ratio(0.85))

        if collide:
            self.game.enemy_collided = True
            if pressed[pygame.K_a]:
                self.rect.x += PLAYER_SPEED
            elif pressed[pygame.K_d]:
                self.rect.x -= PLAYER_SPEED
            elif pressed[pygame.K_w]:
                self.rect.y += PLAYER_SPEED
            elif pressed[pygame.K_s]:
                self.rect.y -= PLAYER_SPEED
        else:
            self.game.enemy_collided = False

    def collide_weapon(self):
        collide = pygame.sprite.spritecollide(self, self.game.weapons, True)
        if collide:
            self.sword_equipped = True

    def shoot_sword(self):
        pressed = pygame.key.get_pressed()
        if self.shoot_state == "shoot":
            if self.sword_equipped:
                if pressed[pygame.K_j]:
                    from projectiles.bullet import Bullet
                    Bullet(self.game, self.rect.x, self.rect.y)
                    self.shoot_state = "wait"

    def wait_after_shoot(self):
        if self.shoot_state == "wait":
            self.counter += 1
            if self.counter >= self.wait_time:
                self.counter = 0
                self.shoot_state = "shoot"

    def damage(self, amount):
        self.health = self.health - amount
        self.healthbar.damage(PLAYER_HEALTH, self.health)

        if self.health <= 0:
            self.kill()
            self.healthbar.kill_bar()


class Player_Healthbar(Healthbar):
    def __init__(self, game, player, x, y):
        super().__init__(game, x, y, player)
