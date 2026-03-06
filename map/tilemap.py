import pygame

from settings import *


class GameMode:
    WORLD = "world"
    DUNGEON = "dungeon"
    TMX = "tmx"


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
    TILE_MAP = {
        ".": (0, 0),  # GRASS → трава
        ":": (1, 2),  # SAND → песок
        "T": (1, 4),  # FOREST → кора дерева
        "B": (0, 1),  # MOUNTAIN → камень
        "S": (1, 3),  # SWAMP → гравий
        "~": (1, 2),  # WATER → песок
        "L": (1, 10),  # LAVA → красный камень
        "V": (0, 4),  # VILLAGE → доски
        "H": (0, 4),  # HOUSE → доски
        "N": (0, 4),  # NPC → доски
    }

    def __init__(self, game, x, y, terrain_type="."):
        self.game = game
        self._layer = GROUND_LAYER
        self.groups = game.all_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE
        self.width = TILESIZE
        self.height = TILESIZE

        tile_pos = self.TILE_MAP.get(terrain_type, (0, 0))
        margin = (37 - 32) // 2
        src_x = tile_pos[1] * 37 + margin
        src_y = tile_pos[0] * 37 + margin
        self.image = game.mc_spritesheet.get_image(src_x, src_y, 32, 32)
        if self.width != 32 or self.height != 32:
            self.image = pygame.transform.scale(self.image, (self.width, self.height))
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


class Portal(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = BLOCKS_LAYER
        self.groups = game.all_sprites, game.dungeon_entrances
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE
        self.width = TILESIZE
        self.height = TILESIZE

        try:
            self.image = pygame.image.load("assets/portal.png").convert_alpha()
            self.image = pygame.transform.scale(self.image, (self.width, self.height))
        except:
            self.image = pygame.Surface((self.width, self.height))
            self.image.fill((128, 0, 128))

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

    def update(self):
        collide = pygame.sprite.spritecollide(self, self.game.mainPlayer, False)
        if collide:
            if hasattr(self.game, "mode"):
                if self.game.mode == "world":
                    self.game.enter_dungeon()
                elif self.game.mode == "dungeon":
                    self.game.exit_dungeon()


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


class NPC(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = BLOCKS_LAYER
        self.groups = game.all_sprites, game.npcs
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE
        self.width = CHARACTER_SIZE
        self.height = CHARACTER_SIZE

        try:
            self.image = pygame.image.load("assets/214742.png").convert_alpha()
            self.image = pygame.transform.scale(self.image, (self.width, self.height))
        except:
            self.image = pygame.Surface((self.width, self.height))
            self.image.fill((255, 200, 0))

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y
