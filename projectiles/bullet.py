import pygame

from settings import *


class Bullet(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = PLAYER_LAYER
        self.groups = game.all_sprites, game.bullets
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x
        self.y = y

        self.width = TILESIZE - 2
        self.height = TILESIZE - 2

        self.image = game.bullet_spritesheet.get_image(0, 0, self.width, self.height)
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

        self.direction = game.player.direction
        self.damage = 3

    def move(self):
        if self.direction == "right":
            self.rect.x += BULLET_SPEED
        if self.direction == "left":
            self.rect.x -= BULLET_SPEED
        if self.direction == "up":
            self.rect.y -= BULLET_SPEED
        if self.direction == "down":
            self.rect.y += BULLET_SPEED

    def collide_block(self):
        collide = pygame.sprite.spritecollide(self, self.game.blocks, False)
        if collide:
            self.kill()

    def collide_enemy(self):
        collide = pygame.sprite.spritecollide(self, self.game.enemies, False)
        if collide:
            collide[0].damage(self.damage)
            self.kill()

    def update(self):
        self.move()
        self.collide_enemy()
        self.collide_block()


class Enemy_Bullet(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = ENEMY_LAYER
        self.groups = game.all_sprites, game.bullets
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x
        self.y = y

        self.width = TILESIZE
        self.height = TILESIZE

        self.image = game.bullet_spritesheet.get_image(0, 0, self.width, self.height)
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

        self.direction = game.player.direction
        self.damage = 1

    def move(self):
        if self.direction == "right":
            self.rect.x += BULLET_SPEED
        if self.direction == "left":
            self.rect.x -= BULLET_SPEED
        if self.direction == "up":
            self.rect.y -= BULLET_SPEED
        if self.direction == "down":
            self.rect.y += BULLET_SPEED

    def collide_block(self):
        collide = pygame.sprite.spritecollide(self, self.game.blocks, False)
        if collide:
            self.kill()

    def collide_player(self):
        collide = pygame.sprite.spritecollide(self, self.game.mainPlayer, False)
        if collide:
            collide[0].damage(self.damage)
            self.kill()

    def update(self):
        self.move()
        self.collide_player()
        self.collide_block()
