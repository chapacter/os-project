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

LOOT_ANIMATION_STEP = 5
LOOT_ANIMATION_MAX_ANGLE = 90
LOOT_FLY_DURATION = 30

FOOD_TYPES = {
    0: {
        "name": "food",
        "sheet": "hallowicons.png",
        "grid": (8, 3),
        "row": 0,
        "heal": 3,
        "color": (100, 200, 100),
    },
    1: {
        "name": "berry",
        "sheet": "hallowicons.png",
        "grid": (8, 3),
        "row": 2,
        "heal": 6,
        "color": (200, 100, 100),
    },
}

WEAPON_TYPES = {
    0: {"name": "sword", "sheet": "sword.png", "grid": (3, 1), "col": 0, "damage": 1},
    1: {"name": "axe", "sheet": "sword.png", "grid": (3, 1), "col": 1, "damage": 1},
    2: {"name": "mace", "sheet": "sword.png", "grid": (3, 1), "col": 2, "damage": 1},
}

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
        "chest_closed": (8, 0),
        "chest_open": (8, 1),
        "decoration": (6, 5),
    },
    4: {
        "floor": (6, 9),
        "wall": (2, 3),
        "portal": (1, 2),
        "chest_closed": (8, 0),
        "chest_open": (8, 1),
        "decoration": (4, 4),
    },
}

BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)

SPRITE_PLAYER = {
    "sheet": "assets/player.png",
    "sheet_size": (960, 172),
    "sprite_size": (64, 43),
    "target_size": (64, 43),
    "offset": (32, 21),
    "hitbox_size": 20,
}

SPRITE_ENEMY = {
    "sheet": "assets/enemy/enemy.png",
    "sheet_size": (96, 128),
    "sprite_size": (32, 32),
    "target_size": (32, 32),
    "offset": (16, 16),
    "hitbox_size": 26,
}

ENEMY_TYPES = {
    0: {
        "sheet": "assets/enemy/enemy.png",
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
        "sheet": "assets/enemy/ghost.png",
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
        "sheet": "assets/enemy/reaper.png",
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
        "sheet": "assets/enemy/reaper_blade.png",
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
    4: {
        "sheet": "assets/enemy/sunny-mushroom-breath-no-gas.png",
        "grid": (3, 4),
        "sprite_size": (26, 26),
        "weight": 1,
        "hp": 7,
        "speed_mod": 0.0,
        "detection_range": 300,
        "attack_range": 200,
        "retreat_range": 0,
        "retreat_distance": 0,
        "melee_range": 0,
        "damage": 1,
        "shoot_cooldown": 25,
        "melee_cooldown": 0,
        "always_chase": False,
        "has_blink": False,
    },
    5: {
        "sheet": "assets/enemy/death_knight.png",
        "grid": (3, 4),
        "sprite_size": (48, 64),
        "direction_map": {"up": 0, "right": 1, "down": 2, "left": 3},
        "weight": 1,
        "hp": 7,
        "speed_mod": 0.5,
        "detection_range": 300,
        "attack_range": 200,
        "retreat_range": 0,
        "retreat_distance": 0,
        "melee_range": 0,
        "damage": 1,
        "shoot_cooldown": 25,
        "melee_cooldown": 0,
        "always_chase": True,
        "has_blink": False,
    },
    6: {
        "sheet": "assets/enemy/dead_lich.png",
        "grid": (3, 4),
        "sprite_size": (48, 64),
        "direction_map": {"up": 0, "right": 1, "down": 2, "left": 3},
        "weight": 1,
        "hp": 7,
        "speed_mod": 0.5,
        "detection_range": 300,
        "attack_range": 200,
        "retreat_range": 0,
        "retreat_distance": 0,
        "melee_range": 0,
        "damage": 1,
        "shoot_cooldown": 25,
        "melee_cooldown": 0,
        "always_chase": True,
        "has_blink": False,
    },
    7: {
        "sheet": "assets/enemy/fallen_warrior.png",
        "grid": (3, 4),
        "sprite_size": (48, 64),
        "direction_map": {"up": 0, "right": 1, "down": 2, "left": 3},
        "weight": 1,
        "hp": 7,
        "speed_mod": 0.5,
        "detection_range": 300,
        "attack_range": 200,
        "retreat_range": 0,
        "retreat_distance": 0,
        "melee_range": 0,
        "damage": 1,
        "shoot_cooldown": 25,
        "melee_cooldown": 0,
        "always_chase": True,
        "has_blink": False,
    },
    8: {
        "sheet": "assets/enemy/BlackWidow.png",
        "grid": (4, 4),
        "sprite_size": (32, 32),
        "frame_move": 4,
        "direction_map": {"down": 0, "right": 1, "up": 2, "left": 3},
        "weight": 1,
        "hp": 7,
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
        "has_blink": False,
    },
    9: {
        "sheet": "assets/enemy/EyeTentacles.png",
        "grid": (4, 4),
        "sprite_size": (32, 32),
        "frame_move": 4,
        "direction_map": {"down": 0, "right": 1, "up": 2, "left": 3},
        "weight": 1,
        "hp": 7,
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
        "has_blink": False,
    },
    10: {
        "sheet": "assets/enemy/toad.png",
        "grid": (4, 4),
        "sprite_size": (32, 32),
        "frame_move": 4,
        "direction_map": {"down": 0, "right": 1, "up": 2, "left": 3},
        "weight": 1,
        "hp": 7,
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
        "has_blink": False,
    },
    11: {
        "sheet": "assets/enemy/witch1.png",
        "grid": (3, 4),
        "sprite_size": (26, 36),
        "weight": 1,
        "hp": 6,
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
        "cone_attack": True,
    },
    12: {
        "sheet": "assets/enemy/witch2.png",
        "grid": (3, 4),
        "sprite_size": (26, 36),
        "weight": 1,
        "hp": 6,
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
        "cone_attack": True,
    },
    13: {
        "sheet": "assets/enemy/jacko_a.png",
        "grid": (3, 4),
        "sprite_size": (26, 36),
        "weight": 1,
        "hp": 11,
        "speed_mod": 1.5,
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
    14: {
        "sheet": "assets/enemy/jacko_b.png",
        "grid": (3, 4),
        "sprite_size": (26, 36),
        "weight": 1,
        "hp": 11,
        "speed_mod": 1.5,
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
}

FLOOR_BOSS_CONFIG = {
    1: {
        "sheet": "assets/enemy/enemy.png",
        "frame_size": (32, 32),
        "grid": (3, 4),
        "frame_move": 3,
        "direction_map": {"down": 0, "left": 1, "right": 2, "up": 3},
        "attack_speed_mult": 1.0,
        "summon_enemy_types": [0, 1, 2, 3],
    },
    2: {
        "sheet": "assets/enemy/death_knight.png",
        "frame_size": (48, 64),
        "grid": (3, 4),
        "frame_move": 3,
        "direction_map": {"up": 0, "right": 1, "down": 2, "left": 3},
        "attack_speed_mult": 1.5,
        "summon_enemy_types": [5, 6, 7],
    },
    3: {
        "sheet": "assets/enemy/EyeTentacles.png",
        "frame_size": (32, 32),
        "grid": (4, 4),
        "frame_move": 4,
        "direction_map": {"down": 0, "right": 1, "up": 2, "left": 3},
        "attack_speed_mult": 2.0,
        "summon_enemy_types": [8, 9, 10],
    },
    4: {
        "sheet": "assets/enemy/horseman_b.png",
        "frame_size": (52, 53),
        "grid": (3, 4),
        "frame_move": 3,
        "direction_map": {"down": 0, "left": 1, "right": 2, "up": 3},
        "attack_speed_mult": 2.5,
        "summon_enemy_types": [11, 12, 13, 14],
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

BOSS_CONFIG = {
    "hp": 50,
    "speed": 1.5,
    "sprite_size": (96, 96),
    "hitbox_size": 60,
    "damage": 2,
    "phase_thresholds": [0.66, 0.33],
    "phase1": {
        "speed": 1.5,
        "attacks": ["chase", "melee", "teleport", "area_damage"],
        "teleport_interval": 180,
        "melee_cooldown": 60,
        "area_cooldown": 180,
        "area_radius": 200,
        "area_particle_count": 16,
    },
    "phase2": {
        "speed": 2.0,
        "attacks": ["chase", "melee", "teleport", "area_damage", "ranged"],
        "teleport_interval": 300,
        "area_radius": 250,
        "area_cooldown": 180,
        "area_particle_count": 20,
        "ranged_cooldown": 240,
    },
    "phase3": {
        "speed": 2.5,
        "attacks": ["chase", "melee", "teleport", "area_damage", "ranged", "summon"],
        "teleport_interval": 300,
        "area_radius": 300,
        "area_cooldown": 180,
        "area_particle_count": 24,
        "ranged_cooldown": 240,
        "summon_count": 5,
        "summon_cooldown": 420,
    },
}
