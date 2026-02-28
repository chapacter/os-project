import pygame

from settings import *


class Block(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = BLOCKS_LAYER
        self.groups = game.all_sprites, game.blocks
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE
        self.width = TILESIZE
        self.height = TILESIZE

        self.image = game.terrain_spritesheet.get_image(0, 19, self.width, self.height)
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y


class Ground(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = GROUND_LAYER
        self.groups = game.all_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE
        self.width = TILESIZE
        self.height = TILESIZE

        self.image = game.terrain_spritesheet.get_image(0, 72, self.width, self.height)
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y


class DungeonEntrance(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = BLOCKS_LAYER
        self.groups = game.all_sprites, game.dungeon_entrances
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE
        self.width = TILESIZE
        self.height = TILESIZE

        self.image = game.terrain_spritesheet.get_image(0, 0, self.width, self.height)
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

    def update(self):
        collide = pygame.sprite.spritecollide(self, self.game.mainPlayer, False)
        if collide:
            self.game.enter_dungeon()


class Decoration(pygame.sprite.Sprite):
    def __init__(self, game, x, y, decor_type="tree"):
        self.game = game
        self._layer = BLOCKS_LAYER - 1
        self.groups = game.all_sprites, game.decorations
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE
        self.width = TILESIZE
        self.height = TILESIZE

        if decor_type == "tree":
            self.image = game.terrain_spritesheet.get_image(
                0, 40, self.width, self.height
            )
        else:
            self.image = game.terrain_spritesheet.get_image(
                0, 19, self.width, self.height
            )

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y


class Water(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = GROUND_LAYER
        self.groups = game.all_sprites, game.water
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE
        self.width = TILESIZE
        self.height = TILESIZE

        self.image = game.terrain_spritesheet.get_image(0, 52, self.width, self.height)
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y
