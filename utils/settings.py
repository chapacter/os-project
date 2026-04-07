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

CONTACT_KNOCKBACK_FORCE = 8
CONTACT_KNOCKBACK_INTERVAL = 15
KNOCKBACK_DECAY = 0.7
KNOCKBACK_DURATION = 16

ENEMY_LAYER = 3
ENEMY_HEALTH = 6
ENEMY_SPEED = 1
ENEMY_KNOCKBACK_FORCE = 6
ENEMY_KNOCKBACK_DECAY = 0.6

SWORD_KNOCKBACK_FORCE = 6
BULLET_KNOCKBACK_FORCE = 4

WEAPON_LAYER = 7
BULLET_SPEED = 8
BULLET_MAX_DISTANCE = 500

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
ROOMS_PER_FLOOR = 15

FADE_DURATION = 500

FLOOR_THEMES = {
    1: {
        "floor": (0, 5),
        "wall": (0, 0),
        "portal": (1, 1),
        "chest_closed": (9, 0),
        "chest_open": (9, 1),
        "decoration": (1, 0),
    },
    2: {
        "floor": (7, 8),
        "wall": (6, 0),
        "portal": (1, 5),
        "chest_closed": (9, 0),
        "chest_open": (9, 1),
        "decoration": (8, 4),
    },
    3: {
        "floor": (5, 1),
        "wall": (5, 3),
        "portal": (1, 6),
        "chest_closed": (10, 0),
        "chest_open": (10, 1),
        "decoration": (6, 5),
    },
    4: {
        "floor": (7, 9),
        "wall": (2, 3),
        "portal": (1, 3),
        "chest_closed": (10, 0),
        "chest_open": (10, 1),
        "decoration": (4, 4),
    },
}

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
        "hp": 3,
        "speed_mod": 1.0,
        "detection_range": 300,
        "attack_range": 200,
        "retreat_range": 50,
        "retreat_distance": 80,
        "melee_range": 0,
        "damage": 1,
        "shoot_cooldown": 50,
        "melee_cooldown": 0,
        "always_chase": False,
        "has_blink": False,
    },
    1: {
        "sheet": "assets/ghost.png",
        "grid": (3, 4),
        "sprite_size": (26, 36),
        "weight": 1,
        "hp": 2,
        "speed_mod": 2.0,
        "detection_range": 400,
        "attack_range": 0,
        "retreat_range": 0,
        "retreat_distance": 0,
        "melee_range": 80,
        "damage": 1,
        "shoot_cooldown": 0,
        "melee_cooldown": 10,
        "always_chase": True,
        "has_blink": True,
        "blink_interval": 8,
    },
    2: {
        "sheet": "assets/reaper.png",
        "grid": (3, 4),
        "sprite_size": (26, 36),
        "weight": 1,
        "hp": 7,
        "speed_mod": 0.5,
        "detection_range": 400,
        "attack_range": 0,
        "retreat_range": 0,
        "retreat_distance": 0,
        "melee_range": 50,
        "damage": 4,
        "shoot_cooldown": 0,
        "melee_cooldown": 60,
        "always_chase": True,
        "has_blink": False,
    },
    3: {
        "sheet": "assets/reaper_blade.png",
        "grid": (3, 4),
        "sprite_size": (32, 36),
        "weight": 1,
        "hp": 9,
        "speed_mod": 0.5,
        "detection_range": 450,
        "attack_range": 0,
        "retreat_range": 0,
        "retreat_distance": 0,
        "melee_range": 60,
        "damage": 3,
        "shoot_cooldown": 0,
        "melee_cooldown": 45,
        "always_chase": True,
        "has_blink": False,
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
