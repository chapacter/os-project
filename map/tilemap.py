import pygame

from utils.settings import *


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

        if game.mode == GameMode.DUNGEON:
            floor = getattr(game, "current_dungeon_floor", 1)
            theme = FLOOR_THEMES.get(floor, FLOOR_THEMES[1])
            row, col = theme["wall"]
            src_x = col * TILESIZE
            src_y = row * TILESIZE
        else:
            src_x = 0
            src_y = 0

        self.image = game.terrain_spritesheet.get_image(
            src_x, src_y, self.width, self.height
        )
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

        if game.physics_enabled and game.physics:
            game.physics.add_static_block(
                self.rect.x,
                self.rect.y,
                self.rect.width,
                self.rect.height,
                f"block_{self.rect.x}_{self.rect.y}",
            )


class Ground(pygame.sprite.Sprite):
    TILE_MAP = {
        ".": (0, 5),  # GRASS → Floor
        ":": (2, 0),  # SAND → Cobblestone
        "T": (3, 0),  # FOREST → Planks
        "B": (2, 0),  # MOUNTAIN → Cobblestone
        "S": (2, 0),  # SWAMP → Cobblestone
        "~": (5, 2),  # WATER → Water
        "L": (2, 0),  # LAVA → Cobblestone
        "V": (3, 0),  # VILLAGE → Planks
        "H": (3, 0),  # HOUSE → Planks
        "N": (3, 0),  # NPC → Planks
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

        if game.mode == GameMode.DUNGEON:
            floor = getattr(game, "current_dungeon_floor", 1)
            theme = FLOOR_THEMES.get(floor, FLOOR_THEMES[1])
            if terrain_type == ".":
                row, col = theme["floor"]
            elif terrain_type == "B":
                row, col = theme["wall"]
            elif terrain_type == "T":
                row, col = theme["decoration"]
            else:
                row, col = theme["floor"]
        else:
            tile_pos = self.TILE_MAP.get(terrain_type, (2, 0))
            row, col = tile_pos

        src_x = col * 32
        src_y = row * 32
        self.image = game.terrain_spritesheet.get_image(src_x, src_y, 32, 32)
        if self.width != 32 or self.height != 32:
            self.image = pygame.transform.scale(self.image, (self.width, self.height))
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y


class DungeonEntrance(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = BLOCKS_LAYER
        self.groups = game.all_sprites, game.dungeon_entrances, game.interactables
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE
        self.width = TILESIZE
        self.height = TILESIZE

        if game.mode == GameMode.DUNGEON:
            floor = getattr(game, "current_dungeon_floor", 1)
            theme = FLOOR_THEMES.get(floor, FLOOR_THEMES[1])
            row, col = theme["portal"]
        else:
            row, col = 1, 5

        src_x = col * TILESIZE
        src_y = row * TILESIZE
        self.image = game.terrain_spritesheet.get_image(
            src_x, src_y, self.width, self.height
        )
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

    def update(self):
        pass

    def interact(self):
        if self.game.mode == GameMode.WORLD:
            self.game.enter_dungeon()
        elif self.game.mode == GameMode.DUNGEON:
            self.game.go_deeper()


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

        if game.mode == GameMode.DUNGEON:
            floor = getattr(game, "current_dungeon_floor", 1)
            theme = FLOOR_THEMES.get(floor, FLOOR_THEMES[1])
            row, col = theme["decoration"]
        else:
            row, col = 1, 0

        src_x = col * TILESIZE
        src_y = row * TILESIZE
        self.image = game.terrain_spritesheet.get_image(
            src_x, src_y, self.width, self.height
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

        self.image = game.terrain_spritesheet.get_image(5, 2, self.width, self.height)
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


class Bed(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = BLOCKS_LAYER - 1
        self.groups = game.all_sprites, game.decorations, game.interactables
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE
        self.width = TILESIZE
        self.height = TILESIZE

        image = pygame.image.load("assets/Bed.png").convert_alpha()
        self.image = pygame.Surface((TILESIZE, TILESIZE), pygame.SRCALPHA)
        bx = (TILESIZE - 23) // 2
        by = TILESIZE - 17
        self.image.blit(image, (bx, by))

        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

        # Real visual bounds for interaction hint (bed sprite: 23x17, bottom-aligned)
        self.visual_rect = pygame.Rect(
            self.x + (TILESIZE - 23) // 2,
            self.y + TILESIZE - 17,
            23, 17
        )

    def interact(self):
        self.game.pause()
