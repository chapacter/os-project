import random
from collections import deque

from map.room import Room, RoomType


class DungeonGenerator:
    def __init__(self, grid_width=4, grid_height=4, seed=None):
        self.seed = seed if seed is not None else random.randint(0, 1000000)
        random.seed(self.seed)

        self.grid_width = grid_width
        self.grid_height = grid_height
        self.rooms = {}
        self.floor_number = 1

    def generate_floor(self, floor_number):
        self.floor_number = floor_number
        self.rooms = {}
        random.seed(self.seed + floor_number)

        self._create_rooms()
        self._connect_rooms()
        self._assign_room_types()

        return self._generate_tile_map()

    def _create_rooms(self):
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                self.rooms[(x, y)] = Room(x, y, RoomType.EMPTY)

    def _connect_rooms(self):
        start_room = (self.grid_width // 2, self.grid_height // 2)

        all_rooms = list(self.rooms.keys())
        random.shuffle(all_rooms)

        visited = {start_room}
        queue = deque([start_room])

        while queue:
            current = queue.popleft()

            neighbors = []
            x, y = current
            if x > 0 and (x - 1, y) not in visited:
                neighbors.append((x - 1, y))
            if x < self.grid_width - 1 and (x + 1, y) not in visited:
                neighbors.append((x + 1, y))
            if y > 0 and (x, y - 1) not in visited:
                neighbors.append((x, y - 1))
            if y < self.grid_height - 1 and (x, y + 1) not in visited:
                neighbors.append((x, y + 1))

            for neighbor in neighbors:
                if neighbor in all_rooms and random.random() < 0.7:
                    direction = self._get_direction(current, neighbor)
                    self.rooms[current].connect_to(self.rooms[neighbor], direction)
                    visited.add(neighbor)
                    queue.append(neighbor)

        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if random.random() < 0.3:
                    neighbors = []
                    if x > 0:
                        neighbors.append((x - 1, y))
                    if x < self.grid_width - 1:
                        neighbors.append((x + 1, y))
                    if y > 0:
                        neighbors.append((x, y - 1))
                    if y < self.grid_height - 1:
                        neighbors.append((x, y + 1))

                    if neighbors:
                        nx, ny = random.choice(neighbors)
                        if not self.rooms[(x, y)].has_door(
                                self._get_direction((x, y), (nx, ny))
                        ):
                            direction = self._get_direction((x, y), (nx, ny))
                            self.rooms[(x, y)].connect_to(
                                self.rooms[(nx, ny)], direction
                            )

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

    def _assign_room_types(self):
        all_coords = list(self.rooms.keys())
        start_x, start_y = self.grid_width // 2, self.grid_height // 2
        start_coord = (start_x, start_y)

        self.rooms[start_coord].room_type = RoomType.START

        farthest = self._find_farthest_room(start_coord)
        self.rooms[farthest].room_type = RoomType.BOSS

        remaining = [c for c in all_coords if c not in [start_coord, farthest]]

        exit_placed = False
        for coord in remaining:
            room = self.rooms[coord]
            if room.room_type == RoomType.EMPTY:
                if not exit_placed and random.random() < 0.3:
                    room.room_type = RoomType.EXIT
                    exit_placed = True
                elif random.random() < 0.5:
                    room.room_type = RoomType.ENEMY
                elif random.random() < 0.3:
                    room.room_type = RoomType.ELITE
                else:
                    room.room_type = RoomType.LOOT

    def _find_farthest_room(self, start):
        max_dist = 0
        farthest = start

        for coord in self.rooms:
            dist = abs(coord[0] - start[0]) + abs(coord[1] - start[1])
            if dist > max_dist:
                max_dist = dist
                farthest = coord

        return farthest

    def _generate_tile_map(self):
        room_tile_width = 7
        room_tile_height = 5
        corridor_length = 3

        total_width = (
                self.grid_width * room_tile_width + (self.grid_width - 1) * corridor_length
        )
        total_height = (
                self.grid_height * room_tile_height
                + (self.grid_height - 1) * corridor_length
        )

        tile_map = [["B" for _ in range(total_width)] for _ in range(total_height)]

        for (gx, gy), room in self.rooms.items():
            room_start_x = gx * (room_tile_width + corridor_length)
            room_start_y = gy * (room_tile_height + corridor_length)

            for ry in range(room_tile_height):
                for rx in range(room_tile_width):
                    tx = room_start_x + rx
                    ty = room_start_y + ry
                    if 0 <= ty < total_height and 0 <= tx < total_width:
                        tile_map[ty][tx] = "."

            for door_dir, has_door in room.doors.items():
                if has_door:
                    if door_dir == "north":
                        for tx in range(
                                room_start_x + 2, room_start_x + room_tile_width - 2
                        ):
                            ty = room_start_y - 1
                            if 0 <= ty < total_height:
                                tile_map[ty][tx] = "."
                    elif door_dir == "south":
                        for tx in range(
                                room_start_x + 2, room_start_x + room_tile_width - 2
                        ):
                            ty = room_start_y + room_tile_height
                            if 0 <= ty < total_height:
                                tile_map[ty][tx] = "."
                    elif door_dir == "east":
                        for ty in range(
                                room_start_y + 2, room_start_y + room_tile_height - 2
                        ):
                            tx = room_start_x + room_tile_width
                            if 0 <= tx < total_width:
                                tile_map[ty][tx] = "."
                    elif door_dir == "west":
                        for ty in range(
                                room_start_y + 2, room_start_y + room_tile_height - 2
                        ):
                            tx = room_start_x - 1
                            if 0 <= tx < total_width:
                                tile_map[ty][tx] = "."

        for y in range(total_height):
            for x in range(total_width):
                if tile_map[y][x] == ".":
                    if y > 0 and tile_map[y - 1][x] == "B":
                        if random.random() < 0.1:
                            tile_map[y][x] = "T"

        return tile_map

    def get_start_position(self):
        for coord, room in self.rooms.items():
            if room.room_type == RoomType.START:
                room_start_x = coord[0] * (7 + 3)
                room_start_y = coord[1] * (5 + 3)
                return room_start_x + 3, room_start_y + 2
        return 3, 2

    def get_boss_position(self):
        for coord, room in self.rooms.items():
            if room.room_type == RoomType.BOSS:
                room_start_x = coord[0] * (7 + 3)
                room_start_y = coord[1] * (5 + 3)
                return room_start_x + 3, room_start_y + 2
        return None

    def get_exit_position(self):
        for coord, room in self.rooms.items():
            if room.room_type == RoomType.EXIT:
                room_start_x = coord[0] * (7 + 3)
                room_start_y = coord[1] * (5 + 3)
                return room_start_x + 3, room_start_y + 2
        return None
