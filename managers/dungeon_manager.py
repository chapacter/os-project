"""DungeonManager — manages dungeon room visibility, building, and transitions.

Extracted incrementally from Game class (main.py) during refactoring.
"""

import random

from entity.boss import Boss
from entity.enemy import Enemy
from items.chest import Chest
from map.door import Door
from map.tilemap import Block, Ground, DungeonEntrance, Decoration, Bed, Wardrobe
from utils import weighted_choice
from utils.settings import TILESIZE, FLOOR_THEMES, ENEMY_TYPES, FLOOR_MUSIC_MAP


class DungeonManager:
    """Handles dungeon room lifecycle: building sprites, sealing, spawning enemies."""

    def __init__(self, game):
        self.game = game

    @property
    def dg(self):
        return self.game.dungeon_generator

    def rebuild_visible_rooms(self):
        """Build Ground/Block/Decoration sprites for visible rooms."""
        game = self.game
        dg = self.dg

        if not hasattr(game, "_tile_map_cache"):
            game._tile_map_cache = dg.generate_floor(game.current_dungeon_floor)
            game._dungeon_built_rooms = set()

        level = game._tile_map_cache

        room_tile_width = dg.room_tile_width
        room_tile_height = dg.room_tile_height
        wall_thickness = dg.wall_thickness
        room_unit_width = room_tile_width + wall_thickness * 2
        room_unit_height = room_tile_height + wall_thickness * 2

        for (gx, gy), room in dg.rooms.items():
            if not room.visible:
                continue
            if (gx, gy) in game._dungeon_built_rooms:
                continue

            game._dungeon_built_rooms.add((gx, gy))

            room_start_x = gx * room_unit_width
            room_start_y = gy * room_unit_height
            room_end_x = room_start_x + room_unit_width
            room_end_y = room_start_y + room_unit_height

            # Build sprites for tiles within room bounds
            for i, row in enumerate(level):
                if i < room_start_y or i >= room_end_y:
                    continue
                for j, column in enumerate(row):
                    if j < room_start_x or j >= room_end_x:
                        continue
                    if column == " ":
                        Ground(game, j, i, " ")
                    elif column == "D":
                        Ground(game, j, i)
                    else:
                        Ground(game, j, i)
                    if column == "B":
                        Block(game, j, i)
                    elif column == "T":
                        Decoration(game, j, i, "tree")
                    elif column == "C":
                        Chest(game, j, i)
                    elif column == "H":
                        Bed(game, j, i)
                    elif column == "W":
                        Wardrobe(game, j, i)
                    elif column == "A":
                        from items.altar import Altar
                        Altar(game, j, i)

            # Build void tiles in a 1-tile margin around the room so adjacent
            # transition tunnels are visible even when the neighbour room isn't.
            void_margin = 1
            void_start_x = max(0, room_start_x - void_margin)
            void_end_x = min(dg.map_width, room_end_x + void_margin)
            void_start_y = max(0, room_start_y - void_margin)
            void_end_y = min(dg.map_height, room_end_y + void_margin)

            for i in range(void_start_y, void_end_y):
                for j in range(void_start_x, void_end_x):
                    if room_start_y <= i < room_end_y and room_start_x <= j < room_end_x:
                        continue
                    if level[i][j] == " ":
                        Ground(game, j, i, " ")

            if room.config and room.config.has_portal:
                boss_pos = dg.get_boss_position()
                if boss_pos:
                    portal = DungeonEntrance(game, boss_pos[0], boss_pos[1])
                    portal.room_coord = (gx, gy)

            self._create_room_doors(game, dg, gx, gy)

    def _create_room_doors(self, game, dg, gx, gy):
        for door_info in dg.get_doors():
            fx, fy = door_info["from_room"]
            if (fx, fy) != (gx, gy):
                continue
            Door(game, door_info["x"], door_info["y"], door_info["direction"],
                 door_info["from_room"], door_info["to_room"],
                 transform=door_info.get("transform"))

    def spawn_enemies(self, room_coord=None):
        """Spawn enemies for visible rooms based on room type."""
        game = self.game
        dg = self.dg

        room_tile_width = dg.room_tile_width
        room_tile_height = dg.room_tile_height
        wall_thickness = dg.wall_thickness
        room_unit_width = room_tile_width + wall_thickness * 2
        room_unit_height = room_tile_height + wall_thickness * 2

        rooms_to_spawn = []
        if room_coord:
            if room_coord in dg.rooms:
                rooms_to_spawn = [room_coord]
        else:
            rooms_to_spawn = [
                (gx, gy)
                for (gx, gy), room in dg.rooms.items()
                if room.visible
            ]

        total_enemies = 0
        spawned_rooms = []
        for gx, gy in rooms_to_spawn:
            room = dg.rooms.get((gx, gy))
            if not room:
                continue
            if room.enemy_count > 0:
                continue
            if room.enemies_spawned:
                continue
            room.enemy_count = 0

            cfg = room.config
            if not cfg:
                continue

            room.enemies_spawned = True

            if cfg.is_boss:
                boss_pos = dg.get_boss_position()
                if boss_pos:
                    Boss(game, boss_pos[0], boss_pos[1], floor=game.current_dungeon_floor)
                    room.enemy_count = 1
                    total_enemies += 1
                    _, boss_music = FLOOR_MUSIC_MAP.get(
                        game.current_dungeon_floor,
                        ("assets/sounds/Music.ogg", "assets/sounds/Boss.ogg"),
                    )
                    game.services.audio.load_music(boss_music)
                    mult = 1.5 if game.current_dungeon_floor == 3 else 1.0
                    game.services.audio.play_music(context="dungeon", volume_multiplier=mult)

                if cfg.spawn_weak_count > 0:
                    room_start_x = gx * room_unit_width + wall_thickness
                    room_start_y = gy * room_unit_height + wall_thickness
                    margin = 2
                    for _ in range(cfg.spawn_weak_count):
                        enemy_type = self._pick_enemy_type(game.current_dungeon_floor)
                        ex = random.randint(
                            room_start_x + margin,
                            room_start_x + room_tile_width - 1 - margin,
                        )
                        ey = random.randint(
                            room_start_y + margin,
                            room_start_y + room_tile_height - 1 - margin,
                        )
                        Enemy(game, ex, ey, enemy_type=enemy_type)
                        room.enemy_count += 1
                        total_enemies += 1

                spawned_rooms.append((gx, gy))
                continue

            if not cfg.spawns_enemies:
                continue

            room_start_x = gx * room_unit_width + wall_thickness
            room_start_y = gy * room_unit_height + wall_thickness
            margin = 2
            floor = game.current_dungeon_floor
            min_count, max_count = cfg.spawn_count_range
            hp_mult = cfg.hp_multiplier
            for _ in range(random.randint(min_count, max_count)):
                enemy_type = self._pick_enemy_type(floor)
                ex = random.randint(
                    room_start_x + margin, room_start_x + room_tile_width - 1 - margin
                )
                ey = random.randint(
                    room_start_y + margin, room_start_y + room_tile_height - 1 - margin
                )
                Enemy(game, ex, ey, enemy_type=enemy_type, hp_multiplier=hp_mult)
                room.enemy_count += 1
                total_enemies += 1

            spawned_rooms.append((gx, gy))

        for sr in spawned_rooms:
            self.seal_room(sr)

    def _pick_enemy_type(self, floor):
        if floor == 2:
            return random.choice([5, 6, 7])
        elif floor == 3:
            return random.choice([8, 9, 10])
        elif floor == 4:
            return random.choice([11, 12, 13, 14])
        else:
            type_weights = {k: v["weight"] for k, v in ENEMY_TYPES.items() if k < 4}
            return weighted_choice(type_weights)

    def _get_room_tile_bounds(self, room_coord):
        gx, gy = room_coord
        dg = self.dg
        ruw = dg.room_tile_width + dg.wall_thickness * 2
        ruh = dg.room_tile_height + dg.wall_thickness * 2
        return gx * ruw, gy * ruh, gx * ruw + ruw, gy * ruh + ruh

    def seal_room(self, room_coord):
        game = self.game
        dg = self.dg
        room = dg.rooms.get(room_coord)
        if not room or not room.config or not room.config.seal_on_enter:
            return

        floor = game.current_dungeon_floor
        theme = FLOOR_THEMES.get(floor, FLOOR_THEMES[1])

        wall_key = room.config.wall_theme
        floor_key = room.config.floor_theme
        decor_key = room.config.decor_theme

        x1, y1, x2, y2 = self._get_room_tile_bounds(room_coord)

        # Close all doors within room bounds
        for door in list(game.doors):
            if self._is_sprite_in_room_bounds(door, x1, y1, x2, y2):
                door.close()

        for sprite in list(game.all_sprites):
            if not self._is_sprite_in_room_bounds(sprite, x1, y1, x2, y2):
                continue
            if isinstance(sprite, Block):
                sprite._orig_image = sprite.image
                row, col = theme[wall_key]
                sprite.image = game.terrain_spritesheet.get_image(
                    col * TILESIZE, row * TILESIZE, TILESIZE, TILESIZE
                )
            elif isinstance(sprite, Ground):
                sprite._orig_image = sprite.image
                row, col = theme[floor_key]
                sprite.image = game.terrain_spritesheet.get_image(
                    col * TILESIZE, row * TILESIZE, TILESIZE, TILESIZE
                )
            elif isinstance(sprite, Decoration):
                sprite._orig_image = sprite.image
                row, col = theme[decor_key]
                sprite.image = game.terrain_spritesheet.get_image(
                    col * TILESIZE, row * TILESIZE, TILESIZE, TILESIZE
                )
                game.blocks.add(sprite)
                sprite._battle_block = True

        game._sealed_rooms[room_coord] = {
            "bounds": (x1, y1, x2, y2),
        }

    def unseal_room(self, room_coord):
        game = self.game
        if room_coord not in game._sealed_rooms:
            return

        sealed = game._sealed_rooms.pop(room_coord)
        x1, y1, x2, y2 = sealed.get("bounds", self._get_room_tile_bounds(room_coord))

        for sprite in list(game.all_sprites):
            if not self._is_sprite_in_room_bounds(sprite, x1, y1, x2, y2):
                continue
            if hasattr(sprite, "_battle_block"):
                game.blocks.remove(sprite)
            if hasattr(sprite, "_orig_image"):
                sprite.image = sprite._orig_image

        for door in list(game.doors):
            if self._is_sprite_in_room_bounds(door, x1, y1, x2, y2):
                door.open()

    def _is_sprite_in_room_bounds(self, sprite, x1, y1, x2, y2):
        tx = int(sprite.rect.x / TILESIZE)
        ty = int(sprite.rect.y / TILESIZE)
        return x1 <= tx < x2 and y1 <= ty < y2

    def is_player_fully_inside_room(self):
        """Check if player is fully inside current room (not near door)."""
        game = self.game
        if not hasattr(game, "player") or not game.player:
            return False

        player_tile_x = int(game.player.hitbox.centerx / TILESIZE)
        player_tile_y = int(game.player.hitbox.centery / TILESIZE)

        dg = self.dg
        room_tile_width = dg.room_tile_width
        room_tile_height = dg.room_tile_height
        wall_thickness = dg.wall_thickness
        room_unit_width = room_tile_width + wall_thickness * 2
        room_unit_height = room_tile_height + wall_thickness * 2

        player_room_x = player_tile_x // room_unit_width
        player_room_y = player_tile_y // room_unit_height
        room_coord = (player_room_x, player_room_y)

        room = dg.rooms.get(room_coord)
        if not room:
            return False

        room_start_x = room_coord[0] * room_unit_width + wall_thickness
        room_start_y = room_coord[1] * room_unit_height + wall_thickness
        room_end_x = room_start_x + room_tile_width
        room_end_y = room_start_y + room_tile_height

        door_zone = 1
        return (
                player_tile_x >= room_start_x + door_zone
                and player_tile_x < room_end_x - door_zone
                and player_tile_y >= room_start_y + door_zone
                and player_tile_y < room_end_y - door_zone
        )

    def show_room(self, room_coord):
        """Mark room as visible/visited."""
        if room_coord in self.dg.rooms:
            self.dg.rooms[room_coord].set_visible(True)
            self.dg.rooms[room_coord].set_visited(True)

    def transition_to_room(self, room_coord, direction):
        """Handle room transition when player walks through a door."""
        if room_coord not in self.dg.rooms:
            return
        self.show_room(room_coord)
        self.rebuild_visible_rooms()
