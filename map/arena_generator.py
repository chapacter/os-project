import random


class ArenaGenerator:
    def __init__(self, width=120, height=100, seed=None):
        self.width = width
        self.height = height
        self.seed = seed if seed is not None else random.randint(0, 1000000)
        random.seed(self.seed)

    def generate(self):
        level = [["B" for _ in range(self.width)] for _ in range(self.height)]

        rooms = self._create_rooms(level)
        self._connect_rooms(level, rooms)
        self._place_player(level, rooms)
        self._place_initial_enemies(level)

        return level, rooms

    def _create_rooms(self, level):
        rooms = []
        num_rooms = random.randint(8, 15)
        min_size = 6
        max_size = 14
        attempts = 0
        max_attempts = 500

        while len(rooms) < num_rooms and attempts < max_attempts:
            attempts += 1
            rw = random.randint(min_size, max_size)
            rh = random.randint(min_size, max_size)
            rx = random.randint(2, self.width - rw - 2)
            ry = random.randint(2, self.height - rh - 2)

            new_rect = (rx, ry, rw, rh)
            if self._room_overlaps(new_rect, rooms, padding=3):
                continue

            for y in range(ry, ry + rh):
                for x in range(rx, rx + rw):
                    if 0 <= y < self.height and 0 <= x < self.width:
                        level[y][x] = " "

            rooms.append({"rect": new_rect, "center": (rx + rw // 2, ry + rh // 2)})

        return rooms

    def _room_overlaps(self, rect, rooms, padding=3):
        rx, ry, rw, rh = rect
        for room in rooms:
            ox, oy, ow, oh = room["rect"]
            if (
                    rx - padding < ox + ow
                    and rx + rw + padding > ox
                    and ry - padding < oy + oh
                    and ry + rh + padding > oy
            ):
                return True
        return False

    def _connect_rooms(self, level, rooms):
        if len(rooms) < 2:
            return

        connected = {0}
        unconnected = set(range(1, len(rooms)))

        while unconnected:
            best_dist = float("inf")
            best_pair = None

            for c in connected:
                for u in unconnected:
                    cx, cy = rooms[c]["center"]
                    ux, uy = rooms[u]["center"]
                    dist = abs(cx - ux) + abs(cy - uy)
                    if dist < best_dist:
                        best_dist = dist
                        best_pair = (c, u)

            if best_pair is None:
                break

            c, u = best_pair
            self._carve_corridor(level, rooms[c]["center"], rooms[u]["center"])
            connected.add(u)
            unconnected.remove(u)

        for _ in range(len(rooms) // 3):
            a = random.randint(0, len(rooms) - 1)
            b = random.randint(0, len(rooms) - 1)
            if a != b:
                self._carve_corridor(level, rooms[a]["center"], rooms[b]["center"])

    def _carve_corridor(self, level, start, end):
        x, y = start
        ex, ey = end

        if random.random() < 0.5:
            while x != ex:
                if 0 <= y < self.height and 0 <= x < self.width:
                    level[y][x] = " "
                    if x + 1 < self.width:
                        level[y][x + 1] = " "
                x += 1 if ex > x else -1
            while y != ey:
                if 0 <= y < self.height and 0 <= x < self.width:
                    level[y][x] = " "
                    if y + 1 < self.height:
                        level[y + 1][x] = " "
                y += 1 if ey > y else -1
        else:
            while y != ey:
                if 0 <= y < self.height and 0 <= x < self.width:
                    level[y][x] = " "
                    if y + 1 < self.height:
                        level[y + 1][x] = " "
                y += 1 if ey > y else -1
            while x != ex:
                if 0 <= y < self.height and 0 <= x < self.width:
                    level[y][x] = " "
                    if x + 1 < self.width:
                        level[y][x + 1] = " "
                x += 1 if ex > x else -1

    def _place_player(self, level, rooms):
        first = rooms[0]["center"]
        x, y = first
        if 0 <= y < self.height and 0 <= x < self.width:
            level[y][x] = "P"

    def _place_initial_enemies(self, level):
        count = random.randint(5, 10)
        placed = 0
        attempts = 0
        while placed < count and attempts < 5000:
            attempts += 1
            x = random.randint(2, self.width - 3)
            y = random.randint(2, self.height - 3)
            if level[y][x] == " ":
                level[y][x] = "E"
                placed += 1

    def get_enemy_spawn_positions(self, level, player_x, player_y, min_distance=150, count=1):
        positions = []
        attempts = 0
        while len(positions) < count and attempts < 500:
            attempts += 1
            x = random.randint(2, self.width - 3)
            y = random.randint(2, self.height - 3)
            if level[y][x] == " ":
                dx = x - player_x
                dy = y - player_y
                dist = (dx * dx + dy * dy) ** 0.5
                if dist >= min_distance:
                    # Где-то тут должна быть проверка, чтобы враги спавнились не слишком близко
                    positions.append((x, y))
        return positions
