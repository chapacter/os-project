import random
from collections import deque

from map.room import Room, RoomType


class DungeonGenerator:
    def __init__(self, grid_width=8, grid_height=8, seed=None):
        self.seed = seed if seed is not None else random.randint(0, 1000000)
        random.seed(self.seed)

        self.grid_width = grid_width
        self.grid_height = grid_height
        self.rooms = {}
        self.floor_number = 1

        self.room_tile_width = random.randint(12, 16)
        self.room_tile_height = random.randint(12, 16)
        self.wall_thickness = 1
        self.door_width = 2

    def get_room_size(self):
        return self.room_tile_width, self.room_tile_height

    def get_wall_thickness(self):
        return self.wall_thickness

    def get_door_width(self):
        return self.door_width

    def get_center_position(self):
        room_tile_width = self.room_tile_width
        room_tile_height = self.room_tile_height
        wall_thickness = self.wall_thickness
        room_unit_width = room_tile_width + wall_thickness * 2
        room_unit_height = room_tile_height + wall_thickness * 2

        center_gx = self.grid_width // 2
        center_gy = self.grid_height // 2

        room_start_x = center_gx * room_unit_width + wall_thickness
        room_start_y = center_gy * room_unit_height + wall_thickness

        return room_start_x + room_tile_width // 2, room_start_y + room_tile_height // 2

    def generate_floor(self, floor_number):
        self.floor_number = floor_number
        self.rooms = {}
        random.seed(self.seed + floor_number)

        self.room_tile_width = random.randint(12, 16)
        self.room_tile_height = random.randint(12, 16)

        self._create_rooms()
        self._connect_rooms()
        self._assign_room_types()

        return self._generate_tile_map()

    def pregenerate_all_floors(self, num_floors=4):
        floors = {}
        for floor in range(1, num_floors + 1):
            floors[floor] = self.generate_floor(floor)
        return floors

    def _create_rooms(self):
        self.rooms = {}
        room_count = random.randint(5, 10)

        # Grid positions that are available (8x8 grid)
        all_positions = [
            (x, y) for x in range(self.grid_width) for y in range(self.grid_height)
        ]

        # Start with a random position for the first room
        start_pos = random.choice(all_positions)
        self.rooms[start_pos] = Room(start_pos[0], start_pos[1], RoomType.EMPTY)

        max_distance = 10
        attempts = 0
        max_attempts = 1000

        while len(self.rooms) < room_count and attempts < max_attempts:
            attempts += 1

            # Find all possible neighboring positions from existing rooms
            candidates = set()
            for gx, gy in self.rooms.keys():
                # Check all 4 directions
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = gx + dx, gy + dy
                    if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                        if (nx, ny) not in self.rooms:
                            candidates.add((nx, ny))

            if not candidates:
                # No more adjacent positions available, stop adding rooms
                break

            # Find candidates that are within max_distance from any existing room
            valid_candidates = []
            for cx, cy in candidates:
                # Check distance to nearest existing room via grid path
                min_dist = float("inf")
                for rx, ry in self.rooms.keys():
                    # Simple path distance - can go through other rooms
                    dist = abs(cx - rx) + abs(cy - ry)
                    if dist < min_dist:
                        min_dist = dist

                # Calculate approximate door-to-door distance
                # Each room is roughly room_unit_size tiles
                room_unit_width = self.room_tile_width + self.wall_thickness * 2
                room_unit_height = self.room_tile_height + self.wall_thickness * 2

                # Door distance = grid_distance * room_size + door_offset
                # Approximate: grid_distance * average_room_size - door_offset
                approx_door_dist = (
                        min_dist * ((room_unit_width + room_unit_height) // 2)
                        - self.door_width
                )

                if approx_door_dist <= max_distance * self.room_tile_width:
                    valid_candidates.append((cx, cy, approx_door_dist))

            if valid_candidates:
                # Pick a random valid candidate (prefer closer ones slightly)
                valid_candidates.sort(key=lambda x: x[2])
                if len(valid_candidates) > 2:
                    choice = random.choice(valid_candidates[:3])
                else:
                    choice = random.choice(valid_candidates)
                cx, cy, _ = choice
                self.rooms[(cx, cy)] = Room(cx, cy, RoomType.EMPTY)
            else:
                # Increase max_distance and try again
                max_distance += 1
                if max_distance > 20:
                    # Just use what we have
                    break

        print(
            f"[DEBUG] Created {len(self.rooms)} rooms with max_distance={max_distance}"
        )

    def _calculate_door_distance(self, room1_coord, room2_coord):
        """Calculate shortest path distance from door to door between two rooms using BFS."""
        gx1, gy1 = room1_coord
        gx2, gy2 = room2_coord

        room_unit_width = self.room_tile_width + self.wall_thickness * 2
        room_unit_height = self.room_tile_height + self.wall_thickness * 2

        # Start position (door of room1)
        # For simplicity, use center of room1
        start_x = (
                gx1 * room_unit_width + self.wall_thickness + self.room_tile_width // 2
        )
        start_y = (
                gy1 * room_unit_height + self.wall_thickness + self.room_tile_height // 2
        )

        # End position (door of room2)
        end_x = gx2 * room_unit_width + self.wall_thickness + self.room_tile_width // 2
        end_y = (
                gy2 * room_unit_height + self.wall_thickness + self.room_tile_height // 2
        )

        # BFS to find shortest path through connected rooms
        # State: (gx, gy) - we're in this room's grid cell
        # From each room, we can go to neighboring rooms that are connected

        visited = set()
        queue = deque()
        queue.append((gx1, gy1, 0))  # (room_gx, room_gy, distance in tiles)
        visited.add((gx1, gy1))

        while queue:
            cx, cy, dist = queue.popleft()

            if (cx, cy) == (gx2, gy2):
                # We reached the target room
                # Add the distance from door to room center
                # and from room center to door
                # Approximate: dist * room_unit_size + door_offset
                return dist * max(room_unit_width, room_unit_height)

            # Check connected neighbors (rooms that have doors to each other)
            current_room = self.rooms.get((cx, cy))
            if not current_room:
                continue

            for direction in ["north", "south", "east", "west"]:
                if not current_room.has_door(direction):
                    continue

                # Get neighbor room coordinate
                if direction == "north":
                    nx, ny = cx, cy - 1
                elif direction == "south":
                    nx, ny = cx, cy + 1
                elif direction == "east":
                    nx, ny = cx + 1, cy
                elif direction == "west":
                    nx, ny = cx - 1, cy
                else:
                    continue

                if (nx, ny) not in visited and (nx, ny) in self.rooms:
                    visited.add((nx, ny))
                    # Add distance through this door
                    # Each "hop" through a room is roughly room_unit_size tiles
                    queue.append(
                        (nx, ny, dist + max(room_unit_width, room_unit_height))
                    )

        # If no path found, return infinity
        return float("inf")

    def _connect_rooms(self):
        """Connect rooms using MST (Prim's algorithm) + additional random connections."""
        if len(self.rooms) <= 1:
            return

        room_coords = list(self.rooms.keys())

        # Prim's algorithm to find MST
        in_mst = set()
        not_in_mst = set(room_coords)

        # Start from a random room
        start = random.choice(room_coords)
        in_mst.add(start)
        not_in_mst.remove(start)

        edges = []  # (distance, room1, room2)

        while not_in_mst:
            # Find minimum edge from any room in MST to any room not in MST
            min_edge = None
            min_dist = float("inf")

            for in_room in in_mst:
                for out_room in not_in_mst:
                    # Calculate distance
                    dist = abs(in_room[0] - out_room[0]) + abs(in_room[1] - out_room[1])
                    if dist < min_dist:
                        min_dist = dist
                        min_edge = (in_room, out_room)

            if min_edge:
                in_room, out_room = min_edge
                in_mst.add(out_room)
                not_in_mst.remove(out_room)

                # Connect the rooms
                direction = self._get_direction(in_room, out_room)
                self.rooms[in_room].connect_to(self.rooms[out_room], direction)

        # Add additional random connections (30% chance for nearby rooms)
        for i, room1_coord in enumerate(room_coords):
            for room2_coord in room_coords[i + 1:]:
                if not self.rooms[room1_coord].has_door(
                        self._get_direction(room1_coord, room2_coord)
                ):
                    # Check if rooms are close (within 2 grid cells)
                    dist = abs(room1_coord[0] - room2_coord[0]) + abs(
                        room1_coord[1] - room2_coord[1]
                    )
                    if dist == 1 and random.random() < 0.3:
                        direction = self._get_direction(room1_coord, room2_coord)
                        self.rooms[room1_coord].connect_to(
                            self.rooms[room2_coord], direction
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
        """Assign room types: LOBBY (random), BOSS (farthest), LOOT (1), EVENT (1), others (ENEMY/ELITE)."""
        all_coords = list(self.rooms.keys())

        # LOBBY = random room (player spawns here, no enemies)
        start_coord = random.choice(all_coords)
        self.rooms[start_coord].room_type = RoomType.LOBBY

        # BOSS = farthest from LOBBY
        farthest = self._find_farthest_room(start_coord)
        self.rooms[farthest].room_type = RoomType.BOSS

        # Remaining rooms
        remaining = [c for c in all_coords if c not in [start_coord, farthest]]

        # Exactly 1 LOOT room
        loot_coord = random.choice(remaining)
        self.rooms[loot_coord].room_type = RoomType.LOOT
        remaining.remove(loot_coord)

        # Exactly 1 EVENT room
        event_coord = random.choice(remaining)
        self.rooms[event_coord].room_type = RoomType.EVENT
        remaining.remove(event_coord)

        # Rest: ENEMY (50%) or ELITE (rest)
        random.shuffle(remaining)
        for coord in remaining:
            room = self.rooms[coord]
            if random.random() < 0.5:
                room.room_type = RoomType.ENEMY
            else:
                room.room_type = RoomType.ELITE

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
        room_tile_width = self.room_tile_width
        room_tile_height = self.room_tile_height
        wall_thickness = self.wall_thickness
        door_width = self.door_width

        room_unit_width = room_tile_width + wall_thickness * 2
        room_unit_height = room_tile_height + wall_thickness * 2

        total_width = self.grid_width * room_unit_width
        total_height = self.grid_height * room_unit_height

        tile_map = [["B" for _ in range(total_width)] for _ in range(total_height)]

        for (gx, gy), room in self.rooms.items():
            room_start_x = gx * room_unit_width + wall_thickness
            room_start_y = gy * room_unit_height + wall_thickness

            for ry in range(room_tile_height):
                for rx in range(room_tile_width):
                    tx = room_start_x + rx
                    ty = room_start_y + ry
                    if 0 <= ty < total_height and 0 <= tx < total_width:
                        tile_map[ty][tx] = "."

            room_end_x = room_start_x + room_tile_width
            room_end_y = room_start_y + room_tile_height

            if not room.has_door("north"):
                for rx in range(room_tile_width):
                    tx = room_start_x + rx
                    ty = room_start_y - 1
                    if 0 <= ty < total_height:
                        tile_map[ty][tx] = "B"

            if not room.has_door("south"):
                for rx in range(room_tile_width):
                    tx = room_start_x + rx
                    ty = room_end_y
                    if 0 <= ty < total_height:
                        tile_map[ty][tx] = "B"

            if not room.has_door("west"):
                for ry in range(room_tile_height):
                    tx = room_start_x - 1
                    ty = room_start_y + ry
                    if 0 <= tx < total_width:
                        tile_map[ty][tx] = "B"

            if not room.has_door("east"):
                for ry in range(room_tile_height):
                    tx = room_end_x
                    ty = room_start_y + ry
                    if 0 <= tx < total_width:
                        tile_map[ty][tx] = "B"

        for (gx, gy), room in self.rooms.items():
            room_start_x = gx * room_unit_width + wall_thickness
            room_start_y = gy * room_unit_height + wall_thickness
            room_end_x = room_start_x + room_tile_width
            room_end_y = room_start_y + room_tile_height

            if room.has_door("north") and (gx, gy - 1) in self.rooms:
                for rx in range(door_width):
                    tx = room_start_x + (room_tile_width // 2 - door_width // 2) + rx
                    ty = room_start_y - 1
                    if 0 <= ty < total_height:
                        tile_map[ty][tx] = "."

            if room.has_door("south") and (gx, gy + 1) in self.rooms:
                for rx in range(door_width):
                    tx = room_start_x + (room_tile_width // 2 - door_width // 2) + rx
                    ty = room_end_y
                    if 0 <= ty < total_height:
                        tile_map[ty][tx] = "."

            if room.has_door("west") and (gx - 1, gy) in self.rooms:
                for ry in range(door_width):
                    tx = room_start_x - 1
                    ty = room_start_y + (room_tile_height // 2 - door_width // 2) + ry
                    if 0 <= tx < total_width:
                        tile_map[ty][tx] = "."

            if room.has_door("east") and (gx + 1, gy) in self.rooms:
                for ry in range(door_width):
                    tx = room_end_x
                    ty = room_start_y + (room_tile_height // 2 - door_width // 2) + ry
                    if 0 <= tx < total_width:
                        tile_map[ty][tx] = "."

        for y in range(total_height):
            for x in range(total_width):
                if tile_map[y][x] == ".":
                    if y > 0 and tile_map[y - 1][x] == "B":
                        if random.random() < 0.1:
                            tile_map[y][x] = "T"

        for (gx, gy), room in self.rooms.items():
            if room.room_type == RoomType.LOOT:
                room_start_x = gx * room_unit_width + wall_thickness
                room_start_y = gy * room_unit_height + wall_thickness
                cx = room_start_x + room_tile_width // 2
                cy = room_start_y + room_tile_height // 2
                if 0 <= cy < total_height and 0 <= cx < total_width:
                    tile_map[cy][cx] = "C"

        for (gx, gy), room in self.rooms.items():
            if room.room_type == RoomType.LOBBY:
                room_start_x = gx * room_unit_width + wall_thickness
                room_start_y = gy * room_unit_height + wall_thickness
                cx = room_start_x + room_tile_width // 2
                cy = room_start_y + room_tile_height // 2
                if 0 <= cy < total_height and 0 <= cx < total_width:
                    tile_map[cy][cx] = "H"

                wx = cx + 2
                wy = cy - 1
                wardrobe_tile_size = 3
                if (0 <= wy < total_height and wy + wardrobe_tile_size - 1 < total_height and
                    0 <= wx < total_width and wx + wardrobe_tile_size - 1 < total_width):
                    tile_map[wy][wx] = "W"

        self.map_width = total_width
        self.map_height = total_height

        return tile_map

    def get_start_position(self):
        room_tile_width = self.room_tile_width
        room_tile_height = self.room_tile_height
        wall_thickness = self.wall_thickness
        room_unit_width = room_tile_width + wall_thickness * 2
        room_unit_height = room_tile_height + wall_thickness * 2

        for coord, room in self.rooms.items():
            if room.room_type == RoomType.LOBBY:
                room_start_x = coord[0] * room_unit_width + wall_thickness
                room_start_y = coord[1] * room_unit_height + wall_thickness
                # Spawn in center of room
                return (
                    room_start_x + room_tile_width // 2,
                    room_start_y + room_tile_height // 2,
                )
        return 3, 2

    def get_boss_position(self):
        room_tile_width = self.room_tile_width
        room_tile_height = self.room_tile_height
        wall_thickness = self.wall_thickness
        room_unit_width = room_tile_width + wall_thickness * 2
        room_unit_height = room_tile_height + wall_thickness * 2

        for coord, room in self.rooms.items():
            if room.room_type == RoomType.BOSS:
                room_start_x = coord[0] * room_unit_width + wall_thickness
                room_start_y = coord[1] * room_unit_height + wall_thickness
                return room_start_x + 3, room_start_y + 2
        return None

    def get_event_position(self):
        """Get position in EVENT room."""
        for coord, room in self.rooms.items():
            if room.room_type == RoomType.EVENT:
                room_start_x = coord[0] * room_unit_width + wall_thickness
                room_start_y = coord[1] * room_unit_height + wall_thickness
                return room_start_x + 3, room_start_y + 2
        return None

    def get_doors(self):
        room_tile_width = self.room_tile_width
        room_tile_height = self.room_tile_height
        wall_thickness = self.wall_thickness
        door_width = self.door_width
        room_unit_width = room_tile_width + wall_thickness * 2
        room_unit_height = room_tile_height + wall_thickness * 2

        doors = []
        for (gx, gy), room in self.rooms.items():
            for door_dir, has_door in room.doors.items():
                if has_door:
                    room_start_x = gx * room_unit_width + wall_thickness
                    room_start_y = gy * room_unit_height + wall_thickness
                    room_end_x = room_start_x + room_tile_width
                    room_end_y = room_start_y + room_tile_height

                    door_offset_x = room_tile_width // 2 - door_width // 2
                    door_offset_y = room_tile_height // 2 - door_width // 2

                    if door_dir == "north":
                        x = room_start_x + door_offset_x
                        y = room_start_y - 1
                        to_room = (gx, gy - 1)
                    elif door_dir == "south":
                        x = room_start_x + door_offset_x
                        y = room_end_y
                        to_room = (gx, gy + 1)
                    elif door_dir == "east":
                        x = room_end_x
                        y = room_start_y + door_offset_y
                        to_room = (gx + 1, gy)
                    elif door_dir == "west":
                        x = room_start_x - 1
                        y = room_start_y + door_offset_y
                        to_room = (gx - 1, gy)

                    if to_room in self.rooms:
                        doors.append(
                            {
                                "x": x,
                                "y": y,
                                "direction": door_dir,
                                "from_room": (gx, gy),
                                "to_room": to_room,
                            }
                        )
        return doors

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
        room_tile_width = self.room_tile_width
        room_tile_height = self.room_tile_height
        wall_thickness = self.wall_thickness
        room_unit_width = room_tile_width + wall_thickness * 2
        room_unit_height = room_tile_height + wall_thickness * 2

        room_x = tile_x // room_unit_width
        room_y = tile_y // room_unit_height

        return (room_x, room_y)

    def get_current_room(self, tile_x, tile_y):
        room_coord = self.get_room_at(tile_x, tile_y)
        return self.rooms.get(room_coord)
