import random

from map.models import RoomType
from map.room import Room


class RoomGraph:
    def __init__(self, grid_width=8, grid_height=8, seed=None):
        self.seed = seed if seed is not None else random.randint(0, 1000000)
        random.seed(self.seed)

        self.grid_width = grid_width
        self.grid_height = grid_height
        self.rooms = {}
        self.floor_number = 1

        self.room_tile_width = 16
        self.room_tile_height = 16
        self.wall_thickness = 1
        self.door_width = 2

    @property
    def room_unit_width(self):
        return self.room_tile_width + self.wall_thickness * 2

    @property
    def room_unit_height(self):
        return self.room_tile_height + self.wall_thickness * 2

    def create_rooms(self, room_count=None):
        self.rooms = {}
        count = room_count if room_count is not None else random.randint(5, 10)

        all_positions = [
            (x, y) for x in range(self.grid_width) for y in range(self.grid_height)
        ]

        start_pos = random.choice(all_positions)
        self.rooms[start_pos] = Room(start_pos[0], start_pos[1], RoomType.EMPTY)

        max_distance = 10
        attempts = 0
        max_attempts = 1000

        while len(self.rooms) < count and attempts < max_attempts:
            attempts += 1

            candidates = set()
            for gx, gy in self.rooms.keys():
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = gx + dx, gy + dy
                    if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                        if (nx, ny) not in self.rooms:
                            candidates.add((nx, ny))

            if not candidates:
                break

            valid_candidates = []
            for cx, cy in candidates:
                min_dist = float("inf")
                for rx, ry in self.rooms.keys():
                    dist = abs(cx - rx) + abs(cy - ry)
                    if dist < min_dist:
                        min_dist = dist

                approx_door_dist = (
                        min_dist * ((self.room_unit_width + self.room_unit_height) // 2)
                        - self.door_width
                )

                if approx_door_dist <= max_distance * self.room_tile_width:
                    valid_candidates.append((cx, cy, approx_door_dist))

            if valid_candidates:
                valid_candidates.sort(key=lambda x: x[2])
                if len(valid_candidates) > 2:
                    choice = random.choice(valid_candidates[:3])
                else:
                    choice = random.choice(valid_candidates)
                cx, cy, _ = choice
                self.rooms[(cx, cy)] = Room(cx, cy, RoomType.EMPTY)
            else:
                max_distance += 1
                if max_distance > 20:
                    break

    def connect_rooms(self):
        if len(self.rooms) <= 1:
            return

        room_coords = list(self.rooms.keys())

        in_mst = set()
        not_in_mst = set(room_coords)

        start = random.choice(room_coords)
        in_mst.add(start)
        not_in_mst.remove(start)

        while not_in_mst:
            min_edge = None
            min_dist = float("inf")

            for in_room in in_mst:
                for out_room in not_in_mst:
                    dist = abs(in_room[0] - out_room[0]) + abs(in_room[1] - out_room[1])
                    if dist < min_dist:
                        min_dist = dist
                        min_edge = (in_room, out_room)

            if min_edge:
                in_room, out_room = min_edge
                in_mst.add(out_room)
                not_in_mst.remove(out_room)

                direction = self._get_direction(in_room, out_room)
                self.rooms[in_room].connect_to(self.rooms[out_room], direction)

        for i, room1_coord in enumerate(room_coords):
            for room2_coord in room_coords[i + 1:]:
                if not self.rooms[room1_coord].has_door(
                        self._get_direction(room1_coord, room2_coord)
                ):
                    dist = abs(room1_coord[0] - room2_coord[0]) + abs(
                        room1_coord[1] - room2_coord[1]
                    )
                    if dist == 1 and random.random() < 0.3:
                        direction = self._get_direction(room1_coord, room2_coord)
                        self.rooms[room1_coord].connect_to(
                            self.rooms[room2_coord], direction
                        )

        for (gx, gy), room in list(self.rooms.items()):
            for dx, dy, direction in [(-1, 0, "west"), (1, 0, "east"),
                                      (0, -1, "north"), (0, 1, "south")]:
                nx, ny = gx + dx, gy + dy
                if (nx, ny) in self.rooms and not room.has_door(direction):
                    room.connect_to(self.rooms[(nx, ny)], direction)

    def assign_progression_types(self, has_shop=True, has_altar=True):
        coords = list(self.rooms.keys())
        if not coords:
            return

        lobby = random.choice(coords)
        self.rooms[lobby].room_type = RoomType.LOBBY

        if len(coords) == 1:
            return

        remaining = [c for c in coords if c != lobby]
        remaining.sort(key=lambda c: abs(c[0] - lobby[0]) + abs(c[1] - lobby[1]))

        judge = remaining.pop()
        self.rooms[judge].room_type = RoomType.JUDGE

        if not remaining:
            return

        n = len(remaining)
        guardian_idx = min(n * 2 // 3, n - 1)
        shop_idx = n // 2
        if shop_idx >= guardian_idx:
            shop_idx = max(0, guardian_idx - 1)

        for i, coord in enumerate(remaining):
            room = self.rooms[coord]
            if i == shop_idx and (has_shop or has_altar):
                if has_shop and has_altar:
                    room.room_type = random.choice([RoomType.SHOP, RoomType.ALTAR])
                elif has_shop:
                    room.room_type = RoomType.SHOP
                else:
                    room.room_type = RoomType.ALTAR
            elif i == guardian_idx:
                room.room_type = RoomType.GUARDIAN
            else:
                room.room_type = RoomType.COMBAT

        combat_coords = [c for c in remaining if self.rooms[c].room_type == RoomType.COMBAT]
        bonus_count = min(2, len(combat_coords))
        if bonus_count > 0:
            bonus_coords = random.sample(combat_coords, bonus_count)
            for coord in bonus_coords:
                if random.random() < 0.3:
                    self.rooms[coord].room_type = random.choice([
                        RoomType.LORE, RoomType.SECRET, RoomType.LOOT,
                    ])

    def assign_room_types(self):
        all_coords = list(self.rooms.keys())

        start_coord = random.choice(all_coords)
        self.rooms[start_coord].room_type = RoomType.LOBBY

        farthest = self._find_farthest_room(start_coord)
        self.rooms[farthest].room_type = RoomType.BOSS

        remaining = [c for c in all_coords if c not in [start_coord, farthest]]

        loot_coord = random.choice(remaining)
        self.rooms[loot_coord].room_type = RoomType.LOOT
        remaining.remove(loot_coord)

        event_coord = random.choice(remaining)
        self.rooms[event_coord].room_type = RoomType.EVENT
        remaining.remove(event_coord)

        random.shuffle(remaining)
        for coord in remaining:
            room = self.rooms[coord]
            if random.random() < 0.5:
                room.room_type = RoomType.ENEMY
            else:
                room.room_type = RoomType.ELITE

    def _get_direction(self, from_pos, to_pos):
        fx, fy = from_pos
        tx, ty = to_pos
        if tx < fx:
            return "west"
        elif tx > fx:
            return "east"
        elif ty < fy:
            return "north"
        elif ty > fy:
            return "south"
        return "north"

    def _find_farthest_room(self, start):
        max_dist = 0
        farthest = start
        for coord in self.rooms:
            dist = abs(coord[0] - start[0]) + abs(coord[1] - start[1])
            if dist > max_dist:
                max_dist = dist
                farthest = coord
        return farthest

    def set_start_room_visible(self):
        for coord, room in self.rooms.items():
            if room.room_type == RoomType.LOBBY:
                room.set_visible(True)
                room.set_visited(True)
                break

    def set_room_visible(self, room_coord):
        if room_coord in self.rooms:
            self.rooms[room_coord].set_visible(True)
            self.rooms[room_coord].set_visited(True)

    def get_room_at(self, tile_x, tile_y):
        room_x = tile_x // self.room_unit_width
        room_y = tile_y // self.room_unit_height
        return (room_x, room_y)

    def get_current_room(self, tile_x, tile_y):
        room_coord = self.get_room_at(tile_x, tile_y)
        return self.rooms.get(room_coord)

    def get_start_position(self):
        for coord, room in self.rooms.items():
            if room.room_type == RoomType.LOBBY:
                room_start_x = coord[0] * self.room_unit_width + self.wall_thickness
                room_start_y = coord[1] * self.room_unit_height + self.wall_thickness
                return (
                    room_start_x + self.room_tile_width // 2,
                    room_start_y + self.room_tile_height // 2,
                )
        return 3, 2

    def get_boss_position(self):
        for coord, room in self.rooms.items():
            if room.room_type == RoomType.BOSS:
                room_start_x = coord[0] * self.room_unit_width + self.wall_thickness
                room_start_y = coord[1] * self.room_unit_height + self.wall_thickness
                return room_start_x + 3, room_start_y + 2
        return None

    def get_event_position(self):
        for coord, room in self.rooms.items():
            if room.room_type == RoomType.EVENT:
                room_start_x = coord[0] * self.room_unit_width + self.wall_thickness
                room_start_y = coord[1] * self.room_unit_height + self.wall_thickness
                return room_start_x + 3, room_start_y + 2
        return None
