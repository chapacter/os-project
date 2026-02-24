import math
import pygame

from settings import *


# class Explosion(pygame.sprite.Sprite):
#     def __init__(self, game, x, y):
#         self.game = game
#         self._layer = PLAYER_LAYER
#         self.groups = self.game.all_sprites, self.game.explosion
#         pygame.sprite.Sprite.__init__(self, self.groups)
#
#         self.x = x * TILESIZE
#         self.y = y * TILESIZE
#
#         self.width = TILESIZE
#         self.height = TILESIZE
#
#         self.image = self.game.explosion_spritesheet.get_image(0, 0, self.width, self.height)
#         self.rect = self.image.get_rect()
#         self.rect = self.image.get_rect()
#         self.rect.x = self.x
#         self.rect.y = self.y
#
#         self.damage = 1
#
#         self.animationCounter = 1
#
#     def collide_block(self):
#         collide = pygame.sprite.spritecollide(self, self.game.blocks, False)
#         if collide:
#             self.kill()
#
#     def collide_Player(self):
#         collide = pygame.sprite.spritecollide(self, self.game.mainPlayer, False)
#         if collide:
#             self.game.player.damage(self.damage)
#             self.kill()
#
#     def update(self):
#         self.collide_Player()
#         self.collide_block()
#
#     def explosive(self):
#         pass
#
#     def animation(self):
#         animate = [self.game.enemy_spritesheet.get_image(0, 0, self.width, self.height),
#                    self.game.explosion_spritesheet.get_image(32, 0, self.width, self.height),
#                    self.game.explosion_spritesheet.get_image(64, 0, self.width, self.height),
#                    self.game.explosion_spritesheet.get_image(96, 0, self.width, self.height),
#                    self.game.explosion_spritesheet.get_image(128, 0, self.width, self.height),
#                    self.game.explosion_spritesheet.get_image(160, 0, self.width, self.height),
#                    self.game.explosion_spritesheet.get_image(192, 0, self.width, self.height),
#                    self.game.explosion_spritesheet.get_image(256, 0, self.width, self.height),
#                    self.game.explosion_spritesheet.get_image(288, 0, self.width, self.height),
#                    self.game.explosion_spritesheet.get_image(320, 0, self.width, self.height),
#                    ]
#
#         self.image = animate[math.floor(self.animationCounter)]
#         self.animationCounter += 0.01
#         if self.animationCounter >= 10:
#             # self.animationCounter = 0
#             self.explosive()
#
#     def update(self):
#         self.animation()


class Weapon(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = GROUND_LAYER
        self.groups = self.game.all_sprites, self.game.weapons
        pygame.sprite.Sprite.__init__(self, self.groups)
        
        self.x = x * TILESIZE
        self.y = y * TILESIZE
        
        self.width = TILESIZE
        self.height = TILESIZE
        
        self.image = self.game.weapon_spritesheet.get_image(0, 0, self.width, self.height)
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y
        
        self.animationCounter = 1
    
    def animate(self):
        animation = [self.game.weapon_spritesheet.get_image(0, 0, self.width, self.height),
                     self.game.weapon_spritesheet.get_image(27, 0, self.width, self.height),
                     self.game.weapon_spritesheet.get_image(55, 0, self.width, self.height),]
        self.image = animation[math.floor(self.animationCounter)]
               
        self.animationCounter += 0.02
        if self.animationCounter >= 3:
            self.animationCounter = 0
            
    def update(self):
        self.animate()


# class Bullet(pygame.sprite.Sprite):
#     def __init__(self, game, x, y):
#         self.game = game
#         self._layer = PLAYER_LAYER
#         self.groups = self.game.all_sprites, self.game.bullets
#         pygame.sprite.Sprite.__init__(self, self.groups)
#
#         self.x = x
#         self.y = y
#
#         self.width = TILESIZE - 2
#         self.height = TILESIZE - 2
#
#         self.image = self.game.bullet_spritesheet.get_image(0, 0, self.width, self.height)
#         self.rect = self.image.get_rect()
#         self.rect.x = self.x
#         self.rect.y = self.y
#
#         self.direction = self.game.player.direction
#
#         self.damage = 1
#
#     def move(self):
#
#         if self.direction == "right":
#             self.rect.x += BULLET_SPEED
#
#         if self.direction == "left":
#             self.rect.x -= BULLET_SPEED
#
#         if self.direction == "up":
#             self.rect.y -= BULLET_SPEED
#
#         if self.direction == "down":
#             self.rect.y += BULLET_SPEED
#
#     def collide_block(self):
#         collide = pygame.sprite.spritecollide(self, self.game.blocks, False)
#         if collide:
#             self.kill()
#
#     def collide_Enemy(self):
#         collide = pygame.sprite.spritecollide(self, self.game.enemies, False)
#         if collide:
#             collide[0].damage(self.damage)
#             self.kill()
#
#     def update(self):
#         self.move()
#         self.collide_Enemy()
#         self.collide_block()
#
#
# class Enemy_Bullet(pygame.sprite.Sprite):
#     def __init__(self, game, x, y):
#         self.game = game
#         self._layer = ENEMY_LAYER
#         self.groups = self.game.all_sprites, self.game.bullets
#         pygame.sprite.Sprite.__init__(self, self.groups)
#
#         self.x = x
#         self.y = y
#
#         self.width = TILESIZE
#         self.height = TILESIZE
#
#         self.image = self.game.bullet_spritesheet.get_image(0, 0, self.width, self.height)
#         self.rect = self.image.get_rect()
#         self.rect.x = self.x
#         self.rect.y = self.y
#
#         self.direction = self.game.player.direction
#
#         self.damage = 1
#
#     def move(self):
#
#         if self.direction == "right":
#             self.rect.x += BULLET_SPEED
#
#         if self.direction == "left":
#             self.rect.x -= BULLET_SPEED
#
#         if self.direction == "up":
#             self.rect.y -= BULLET_SPEED
#
#         if self.direction == "down":
#             self.rect.y += BULLET_SPEED
#
#     def collide_block(self):
#         collide = pygame.sprite.spritecollide(self, self.game.blocks, False)
#         if collide:
#             self.kill()
#
#     def collide_Player(self):
#         collide = pygame.sprite.spritecollide(self, self.game.mainPlayer, False)
#         if collide:
#             self.game.player.damage(self.damage)
#             self.kill()
#
#     def update(self):
#         self.move()
#         self.collide_Player()
#         self.collide_block()

# class Projectile(pygame.sprite.Sprite):
#     def __init__(self, game, x, y, entity=None):
#         self.game = game
#         self._layer = entity
#         self.groups = self.game.all_sprites, self.game.bullets
#         pygame.sprite.Sprite.__init__(self, self.groups)
#
#         self.x = x
#         self.y = y
#
#         self.width = TILESIZE - 2
#         self.height = TILESIZE - 2
#
#         self.image = self.game.bullet_spritesheet.get_image(0, 0, self.width, self.height)
#         self.rect = self.image.get_rect()
#         self.rect.x = self.x
#         self.rect.y = self.y
#
#         self.direction = self.game.player.direction
#
#         self.damage = 1
#
#     def move(self):
#         if self.direction == "right":
#             self.rect.x += BULLET_SPEED
#
#         if self.direction == "left":
#             self.rect.x -= BULLET_SPEED
#
#         if self.direction == "up":
#             self.rect.y -= BULLET_SPEED
#
#         if self.direction == "down":
#             self.rect.y += BULLET_SPEED
#
#     def collide_block(self):
#         collide = pygame.sprite.spritecollide(self, self.game.blocks, False)
#         if collide:
#             self.kill()
#
#     def collide_enemy(self):
#         collide = pygame.sprite.spritecollide(self, self.game.enemies, False)
#         if collide:
#             collide[0].damage(self.damage)
#             self.kill()
#
#     def collide_player(self):
#         collide = pygame.sprite.spritecollide(self, self.game.mainPlayer, False)
#         if collide:
#             self.game.player.damage(self.damage)
#             self.kill()
#
#     def update(self):
#         self.move()
#         self.collide_enemy()
#         self.collide_block()
#         self.collide_player()
#
#
# class Bullet(pygame.sprite.Sprite):
#     def __init__(self, game, player, x, y):
#         super().__init__(game, x, y, PLAYER_LAYER)
#
# class Enemy_Bullet(pygame.sprite.Sprite):
#     def __init__(self, game, enemy, x, y):
#         super().__init__(game, self, x, y, ENEMY_LAYER)

class Bullet(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = PLAYER_LAYER
        self.groups = self.game.all_sprites, self.game.bullets
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x
        self.y = y

        self.width = TILESIZE - 2
        self.height = TILESIZE - 2

        self.image = self.game.bullet_spritesheet.get_image(0, 0, self.width, self.height)
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

        self.direction = self.game.player.direction

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

    def collide_Enemy(self):
        collide = pygame.sprite.spritecollide(self, self.game.enemies, False)
        if collide:
            collide[0].damage(self.damage)
            self.kill()

    def update(self):
        self.move()
        self.collide_Enemy()
        self.collide_block()


class Enemy_Bullet(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = ENEMY_LAYER
        self.groups = self.game.all_sprites, self.game.bullets
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x
        self.y = y

        self.width = TILESIZE
        self.height = TILESIZE

        self.image = self.game.bullet_spritesheet.get_image(0, 0, self.width, self.height)
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

        self.direction = self.game.player.direction

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

    def collide_Player(self):
        collide = pygame.sprite.spritecollide(self, self.game.mainPlayer, False)
        if collide:
            self.game.player.damage(self.damage)
            self.kill()

    def update(self):
        self.move()
        self.collide_Player()
        self.collide_block()
