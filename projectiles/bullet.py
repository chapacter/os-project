import pygame

from effects.effect import Effect
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

        self.image, _ = game.effects_spritesheet.get_effect("bullet", SPRITE_EFFECTS)
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
            Effect(self.game, self.rect.centerx, self.rect.centery, "hit")
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

        self.image, _ = game.effects_spritesheet.get_effect("bullet", SPRITE_EFFECTS)
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
            Effect(self.game, self.rect.centerx, self.rect.centery, "hit")
            collide[0].damage(self.damage)
            self.kill()

    def update(self):
        self.move()
        self.collide_player()
        self.collide_block()
