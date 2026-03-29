WIN_WIDTH, WIN_HEIGHT = 1920, 1200

TILESIZE = 32
CHARACTER_SIZE = 26
HITBOXSIZE = 20
HITBOX_WIDTH = 20
HITBOX_HEIGHT = 20
FPS = 60

HEALTH_LAYER = 6

PLAYER_LAYER = 5
PLAYER_HEALTH = 10
PLAYER_SPEED = 5

ENEMY_LAYER = 3
ENEMY_HEALTH = 6
ENEMY_SPEED = 1

WEAPON_LAYER = 7
BULLET_SPEED = 8

BLOCKS_LAYER = 2
GROUND_LAYER = 1

MAP_GENERATOR = "dungeon"

WORLD_SIZE = 3
BIOME_COUNT = 6
WORLD_ZONE_WIDTH = 50
WORLD_ZONE_HEIGHT = 30

DUNGEON_FLOORS = 4
DUNGEON_GRID_WIDTH = 4
DUNGEON_GRID_HEIGHT = 4
ROOMS_PER_FLOOR = 12

FADE_DURATION = 500

BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)

SPRITE_PLAYER = {
    "sheet": "assets/player.png",
    "sheet_size": (960, 172),
    "sprite_size": (64, 43),
    "target_size": (64, 43),
    "offset": (32, 21),
    "hitbox_size": 20,
}

SPRITE_ENEMY = {
    "sheet": "assets/enemy.png",
    "sheet_size": (96, 128),
    "sprite_size": (32, 32),
    "target_size": (32, 32),
    "offset": (16, 16),
    "hitbox_size": 26,
}

ENEMY_TYPES = {
    0: {
        "sheet": "assets/enemy.png",
        "grid": (3, 4),
        "sprite_size": (32, 32),
        "weight": 3,
    },
    1: {
        "sheet": "assets/ghost.png",
        "grid": (3, 4),
        "sprite_size": (26, 36),
        "weight": 1,
    },
    2: {
        "sheet": "assets/reaper.png",
        "grid": (3, 4),
        "sprite_size": (26, 36),
        "weight": 1,
    },
    3: {
        "sheet": "assets/reaper_blade.png",
        "grid": (3, 4),
        "sprite_size": (32, 36),
        "weight": 1,
    },
}

SPRITE_EFFECTS = {
    "sheet": "assets/effects.png",
    "sheet_size": (320, 128),
    "sprite_size": (32, 32),
    "target_size": (32, 32),
    "offset": (16, 16),
    "animation_speed": 0.6,
    "effects": {
        "death": {"row": 0, "frames": 10},
        "grass": {"row": 1, "frames": 5},
        "hit": {"row": 2, "frames": 2},
        "bullet": {"row": 2, "col": 2},
    },
}
