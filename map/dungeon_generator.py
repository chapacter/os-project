import copy
import random

from map.dungeon_generator_old import DungeonGeneratorOld
from map.models import RoomType
from map.providers.json_config_provider import JsonConfigProvider
from map.room import Room
from map.room_graph import RoomGraph

REALM_FLOOR_MAP = {
    1: "entangled_ingress",
    2: "still_bastion",
    3: "wasted_pit",
    4: "living_walls",
    5: "the_old_world",
}

SIDE_MAP = [
    {"north": "north", "south": "south", "east": "east", "west": "west"},
    {"north": "east", "south": "west", "east": "south", "west": "north"},
    {"north": "south", "south": "north", "east": "west", "west": "east"},
    {"north": "west", "south": "east", "east": "north", "west": "south"},
]


def _rotate_coord(x, y, rot, size=18):
    for _ in range(rot):
        x, y = y, size - 1 - x
    return x, y


def _rotate_side(side, rot):
    return SIDE_MAP[rot % 4].get(side, side)


def find_rotation(needed_sides, template_sides):
    needed = set(needed_sides)
    for rot in range(4):
        mapped = {_rotate_side(s, rot) for s in template_sides}
        if mapped == needed:
            return rot
    return None


def _rotate_template(template, rot, room_size=18):
    if rot == 0:
        return template
    t = copy.deepcopy(template)
    W = room_size

    tm = t.get("tile_map", [])
    if isinstance(tm, list) and len(tm) == W:
        grid = [list(row) for row in tm]
        for _ in range(rot):
            grid = [list(col) for col in zip(*grid[::-1])]
        t["tile_map"] = ["".join(row) for row in grid]

    platforms = t.get("platforms", [])
    rotated_platforms = []
    for p in platforms:
        x, y, w, h = p["x"], p["y"], p["width"], p["height"]
        for _ in range(rot):
            nx = y
            ny = W - x - w
            nw = h
            nh = w
            x, y, w, h = nx, ny, nw, nh
        rotated_platforms.append({"x": x, "y": y, "width": w, "height": h})
    t["platforms"] = rotated_platforms

    slots = t.get("spawn_slots", [])
    rotated_slots = []
    for s in slots:
        x, y = _rotate_coord(s["x"], s["y"], rot, W)
        rotated_slots.append({"x": x, "y": y, "slot_type": s.get("slot_type", "floor_a")})
    t["spawn_slots"] = rotated_slots

    door_sides = t.get("door_sides", [])
    t["door_sides"] = [_rotate_side(s, rot) for s in door_sides]

    slots_dict = t.get("slots", {})
    rotated_slots_dict = {}
    for name, zone in slots_dict.items():
        z = dict(zone)
        x1, y1 = _rotate_coord(z["x1"], z["y1"], rot, W)
        x2, y2 = _rotate_coord(z["x2"], z["y2"], rot, W)
        nx1, nx2 = min(x1, x2), max(x1, x2)
        ny1, ny2 = min(y1, y2), max(y1, y2)
        if rot % 2 == 1:
            nw = ny2 - ny1 + 1
            nh = nx2 - nx1 + 1
            z["x1"], z["y1"] = nx1, ny1
            z["x2"], z["y2"] = nx1 + nw - 1, ny1 + nh - 1
        else:
            z["x1"], z["y1"] = nx1, ny1
            z["x2"], z["y2"] = nx2, ny2
        rotated_slots_dict[name] = z
    t["slots"] = rotated_slots_dict

    return t


class DungeonGenerator:
    """New DungeonGenerator with progression path and room templates.

    Two placement modes:
      - "linear":  builds a linear graph LOBBY→COMBAT×N→SHOP/ALTAR→GUARDIAN→COMBAT×N→JUDGE
      - "organic": uses Prim's MST from DungeonGeneratorOld for room placement,
                   then assigns progression types by distance from LOBBY

    Picks room templates from configs and generates tile maps from them.
    Falls back to procedural generation if no templates available.
    """

    def __init__(self, grid_width=4, grid_height=4, seed=None, config_provider=None, placement="linear"):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.seed = seed if seed is not None else random.randint(0, 1000000)
        random.seed(self.seed)
        self.placement = placement

        self.rooms = {}
        self.floor_number = 1
        self.room_tile_width = 18
        self.room_tile_height = 18
        self.wall_thickness = 0
        self.door_width = 2
        self.map_width = 0
        self.map_height = 0

        provider = config_provider or JsonConfigProvider()
        self.realm_configs = provider.get("realm_config")
        self.room_templates = provider.get_room_templates()
        self.room_variants = provider.get_room_variants()
        self._graph = []
        self._room_instances = {}

    def _fallback_generate(self, floor_number):
        old_gen = DungeonGeneratorOld(
            grid_width=self.grid_width,
            grid_height=self.grid_height,
            seed=self.seed,
        )
        tile_map = old_gen.generate_floor(floor_number)
        self.rooms = old_gen.rooms
        self.room_tile_width = old_gen.room_tile_width
        self.room_tile_height = old_gen.room_tile_height
        self.wall_thickness = old_gen.wall_thickness
        self.map_width = old_gen.map_width
        self.map_height = old_gen.map_height
        return tile_map

    def generate_floor(self, floor_number):
        self.floor_number = floor_number
        self.rooms = {}
        random.seed(self.seed + floor_number)
        self._internal_seed = self.seed + floor_number

        self.room_tile_width = 18
        self.room_tile_height = 18

        realm_id = REALM_FLOOR_MAP.get(floor_number, "entangled_ingress")
        realm = self.realm_configs.get(realm_id, {})
        if not realm:
            return self._fallback_generate(floor_number)

        self._realm_id = realm_id
        self._realm = realm

        templates = self._get_templates_for_realm(realm_id)
        if not templates:
            return self._fallback_generate(floor_number)

        if self.placement == "organic":
            return self._generate_organic(floor_number, realm, templates)

        graph = self._build_main_path(realm)
        graph = self._add_optional_branches(graph)
        self._graph = graph

        self.grid_width = len(graph)
        self.grid_height = 1
        self._assign_grid_positions(graph)
        self._connect_graph_rooms(graph)
        self._assign_templates(graph, templates)
        self._validate_graph(graph)

        return self._generate_tile_map_from_templates(graph)

    def _generate_organic(self, floor_number, realm, templates):
        graph = RoomGraph(grid_width=8, grid_height=8, seed=self.seed + floor_number)
        graph.room_tile_width = self.room_tile_width
        graph.room_tile_height = self.room_tile_height
        graph.wall_thickness = self.wall_thickness
        graph.door_width = self.door_width

        room_count = realm.get("min_combat_rooms", 3) + realm.get("max_combat_rooms", 3) + 4
        graph.create_rooms(room_count=room_count)
        graph.connect_rooms()
        graph.assign_progression_types(
            has_shop=realm.get("has_shop", True),
            has_altar=realm.get("has_altar", True),
        )

        self.rooms = graph.rooms
        self.grid_width = graph.grid_width
        self.grid_height = graph.grid_height
        self.room_tile_width = graph.room_tile_width
        self.room_tile_height = graph.room_tile_height
        self.wall_thickness = graph.wall_thickness

        self._assign_templates_organic(templates)
        return self._generate_tile_map_from_templates(init_void=True)

    def _get_templates_for_realm(self, realm_id):
        return [
            t for t in self.room_templates.values()
            if isinstance(t, dict) and t.get("realm_id") == realm_id
        ]

    def _build_main_path(self, realm):
        nodes = []
        rng = random.random

        min_combat = realm.get("min_combat_rooms", 2)
        max_combat = realm.get("max_combat_rooms", 3)
        guardian_count = realm.get("guardian_count", 1)
        has_shop = realm.get("has_shop", True)
        has_altar = realm.get("has_altar", True)

        nodes.append(("lobby", "LOBBY"))

        pre_combat = random.randint(min_combat, max_combat)
        for i in range(pre_combat):
            nodes.append((f"combat_pre_{i}", "COMBAT"))

        special_count = 0
        if has_shop and has_altar:
            if rng() < 0.5:
                nodes.append(("shop", "SHOP"))
                special_count += 1
            else:
                nodes.append(("altar", "ALTAR"))
                special_count += 1
        elif has_shop:
            nodes.append(("shop", "SHOP"))
            special_count += 1
        elif has_altar:
            nodes.append(("altar", "ALTAR"))
            special_count += 1

        for i in range(guardian_count):
            nodes.append((f"guardian_{i}", "GUARDIAN"))

        post_guardian_combat = max(1, random.randint(min_combat, max_combat) // 2)
        for i in range(post_guardian_combat):
            nodes.append((f"combat_post_{i}", "COMBAT"))

        nodes.append(("judge", "JUDGE"))

        return nodes

    def _add_optional_branches(self, graph):
        rng = random.random
        branches = []

        if rng() < 0.4:
            branches.append((None, "secret", "SECRET"))
        if rng() < 0.3:
            branches.append((None, "lore", "LORE"))
        if rng() < 0.5:
            branches.append((None, "loot", "LOOT"))

        result = list(graph)
        for parent_id, node_id, node_type in branches:
            idx = random.randint(0, len(result) - 2)
            result.insert(idx + 1, (node_id, node_type))

        return result

    def _assign_grid_positions(self, graph):
        self.rooms = {}
        max_rooms = self.grid_width * self.grid_height
        count = min(len(graph), max_rooms)

        for i in range(count):
            row = i // self.grid_width
            col = i % self.grid_width
            nid, ntype = graph[i]
            room_type = self._str_to_roomtype(ntype)
            room = Room(col, row, room_type)
            self.rooms[(col, row)] = room

    def _connect_graph_rooms(self, graph):
        room_list = list(self.rooms.items())
        for i in range(len(room_list) - 1):
            (x1, y1), room1 = room_list[i]
            (x2, y2), room2 = room_list[i + 1]
            dx = x2 - x1
            dy = y2 - y1
            if dx == 1:
                room1.connect_to(room2, "east")
            elif dx == -1:
                room1.connect_to(room2, "west")
            elif dy == 1:
                room1.connect_to(room2, "south")
            elif dy == -1:
                room1.connect_to(room2, "north")

    def _str_to_roomtype(self, type_str):
        mapping = {
            "LOBBY": RoomType.LOBBY,
            "COMBAT": RoomType.COMBAT,
            "GUARDIAN": RoomType.GUARDIAN,
            "JUDGE": RoomType.JUDGE,
            "SHOP": RoomType.SHOP,
            "ALTAR": RoomType.ALTAR,
            "LORE": RoomType.LORE,
            "SECRET": RoomType.SECRET,
            "LOOT": RoomType.LOOT,
            "BOSS": RoomType.BOSS,
        }
        return mapping.get(type_str, RoomType.EMPTY)

    def _get_template_for_node(self, node_type_str, templates, needed_sides=None):
        type_map = {
            "LOBBY": "lobby",
            "COMBAT": "combat",
            "GUARDIAN": "guardian",
            "JUDGE": "judge",
            "SHOP": "shop",
            "ALTAR": "altar",
            "LORE": "lore",
            "SECRET": "secret",
            "LOOT": "loot",
        }
        rt = type_map.get(node_type_str)
        if not rt:
            return None, 0

        candidates = [t for t in templates if t.get("room_type") == rt]
        if not candidates:
            return None, 0

        if needed_sides is not None:
            door_count = len(needed_sides)
            candidates = [t for t in candidates if len(t.get("door_sides", [])) == door_count]
            random.shuffle(candidates)
            for t in candidates:
                rot = find_rotation(needed_sides, t.get("door_sides", []))
                if rot is not None:
                    return t, rot
            return None, 0

        return random.choice(candidates), 0

    def _roomtype_to_str(self, room_type):
        mapping = {
            RoomType.LOBBY: "LOBBY",
            RoomType.COMBAT: "COMBAT",
            RoomType.GUARDIAN: "GUARDIAN",
            RoomType.JUDGE: "JUDGE",
            RoomType.SHOP: "SHOP",
            RoomType.ALTAR: "ALTAR",
            RoomType.LORE: "LORE",
            RoomType.SECRET: "SECRET",
            RoomType.LOOT: "LOOT",
            RoomType.BOSS: "BOSS",
        }
        return mapping.get(room_type, "COMBAT")

    def _assign_templates_organic(self, templates):
        self._room_instances = {}
        for coord, room in self.rooms.items():
            needed_sides = {s for s in ["north", "south", "east", "west"] if room.has_door(s)}
            type_str = self._roomtype_to_str(room.room_type)
            template, rot = self._get_template_for_node(type_str, templates, needed_sides)
            if template:
                rotated = _rotate_template(template, rot, room_size=self.room_tile_width)
                self._room_instances[coord] = {
                    "template": rotated,
                    "node_type": type_str,
                    "rotation": rot,
                }

    def _assign_templates(self, graph, templates):
        self._room_instances = {}
        room_list = list(self.rooms.items())

        for i, (coord, room) in enumerate(room_list):
            if i < len(graph):
                nid, ntype = graph[i]
                needed_sides = {s for s in ["north", "south", "east", "west"] if room.has_door(s)}
                template, rot = self._get_template_for_node(ntype, templates, needed_sides)
                if template:
                    rotated = _rotate_template(template, rot, room_size=self.room_tile_width)
                    self._room_instances[coord] = {
                        "template": rotated,
                        "node_type": ntype,
                        "rotation": rot,
                    }

    def _validate_graph(self, graph):
        has_lobby = any(t == "LOBBY" for _, t in graph)
        has_judge = any(t == "JUDGE" for _, t in graph)
        lobby_idx = None
        judge_idx = None
        for i, (_, t) in enumerate(graph):
            if t == "LOBBY":
                lobby_idx = i
            if t == "JUDGE":
                judge_idx = i
        if lobby_idx is not None and judge_idx is not None and lobby_idx > judge_idx:
            pass

    def get_doors(self):
        rw = self.room_unit_width
        rh = self.room_unit_height
        doors = []
        for (gx, gy), room in self.rooms.items():
            for direction, has_door in room.doors.items():
                if not has_door:
                    continue
                horizontal = direction in ("north", "south")
                if horizontal:
                    pos1 = {"x": gx * rw + 8, "y": gy * rh + (1 if direction == "north" else 16), "transform": None}
                    pos2 = {"x": gx * rw + 9, "y": gy * rh + (1 if direction == "north" else 16), "transform": "flip_h"}
                else:
                    x = gx * rw + (16 if direction == "east" else 1)
                    pos1 = {"x": x, "y": gy * rh + 8, "transform": "rotate_90"}
                    pos2 = {"x": x, "y": gy * rh + 9, "transform": "rotate_270"}
                to_room = {
                    "east": (gx + 1, gy),
                    "west": (gx - 1, gy),
                    "north": (gx, gy - 1),
                    "south": (gx, gy + 1),
                }[direction]
                if to_room not in self.rooms:
                    continue
                for pos in (pos1, pos2):
                    doors.append({
                        "x": pos["x"],
                        "y": pos["y"],
                        "direction": direction,
                        "from_room": (gx, gy),
                        "to_room": to_room,
                        "transform": pos["transform"],
                    })
        return doors

    def _generate_tile_map_from_templates(self, graph=None, init_void=False):
        room_tile_width = self.room_tile_width
        room_tile_height = self.room_tile_height
        rw = self.room_unit_width
        rh = self.room_unit_height

        total_width = self.grid_width * rw
        total_height = self.grid_height * rh

        init_char = " " if init_void else "."
        tile_map = [[init_char for _ in range(total_width)] for _ in range(total_height)]

        for (gx, gy), room in self.rooms.items():
            instance = self._room_instances.get((gx, gy))
            template = instance.get("template") if instance else None

            room_start_x = gx * rw
            room_start_y = gy * rh

            if template and "tile_map" in template:
                tm = template["tile_map"]
                for ry in range(room_tile_height):
                    row = tm[ry] if ry < len(tm) else ""
                    for rx in range(room_tile_width):
                        ch = row[rx] if rx < len(row) else "."
                        tx = room_start_x + rx
                        ty = room_start_y + ry
                        if 0 <= ty < total_height and 0 <= tx < total_width:
                            tile_map[ty][tx] = ch
            else:
                for ry in range(room_tile_height):
                    for rx in range(room_tile_width):
                        tx = room_start_x + rx
                        ty = room_start_y + ry
                        if not (0 <= ty < total_height and 0 <= tx < total_width):
                            continue
                        outer = ry == 0 or ry == room_tile_height - 1 or rx == 0 or rx == room_tile_width - 1
                        if outer:
                            tile_map[ty][tx] = " "
                            continue
                        on_north = ry == 1
                        on_south = ry == room_tile_height - 2
                        on_west = rx == 1
                        on_east = rx == room_tile_width - 2
                        is_door = False
                        if on_north and room.has_door("north") and rx in (8, 9):
                            is_door = True
                        if on_south and room.has_door("south") and rx in (8, 9):
                            is_door = True
                        if on_west and room.has_door("west") and ry in (8, 9):
                            is_door = True
                        if on_east and room.has_door("east") and ry in (8, 9):
                            is_door = True
                        if on_north or on_south or on_west or on_east:
                            tile_map[ty][tx] = "D" if is_door else "B"
                        else:
                            tile_map[ty][tx] = "."

        for y in range(total_height):
            for x in range(total_width):
                if tile_map[y][x] == "." and y > 0 and tile_map[y - 1][x] == "B":
                    if random.random() < 0.1:
                        tile_map[y][x] = "T"

        for (gx, gy), room in self.rooms.items():
            room_start_x = gx * rw
            room_start_y = gy * rh

            # Skip special markers if room has a template — template controls its own layout
            if self._room_instances.get((gx, gy), {}).get("template"):
                continue

            if room.room_type in (RoomType.LOOT, RoomType.SECRET):
                cx = room_start_x + room_tile_width // 2
                cy = room_start_y + room_tile_height // 2
                if 0 <= cy < total_height and 0 <= cx < total_width:
                    tile_map[cy][cx] = "C"

            if room.room_type == RoomType.LOBBY:
                cx = room_start_x + room_tile_width // 2
                cy = room_start_y + room_tile_height // 2
                if 0 <= cy < total_height and 0 <= cx < total_width:
                    tile_map[cy][cx] = "H"
                wx = cx + 2
                wy = cy - 1
                if 0 <= wy < total_height and 0 <= wx < total_width:
                    tile_map[wy][wx] = "W"

        self.map_width = total_width
        self.map_height = total_height

        return tile_map

    def get_boss_position(self):
        rw = self.room_unit_width
        rh = self.room_unit_height
        for coord, room in self.rooms.items():
            if room.room_type in (RoomType.BOSS, RoomType.JUDGE):
                room_start_x = coord[0] * rw
                room_start_y = coord[1] * rh
                return room_start_x + 3, room_start_y + 2
        return None

    def get_event_position(self):
        rw = self.room_unit_width
        rh = self.room_unit_height
        for coord, room in self.rooms.items():
            if room.room_type == RoomType.LORE:
                room_start_x = coord[0] * rw
                room_start_y = coord[1] * rh
                return room_start_x + 3, room_start_y + 2
            if room.room_type == RoomType.EVENT:
                room_start_x = coord[0] * rw
                room_start_y = coord[1] * rh
                return room_start_x + 3, room_start_y + 2
        return None

    @property
    def room_unit_width(self):
        return self.room_tile_width + self.wall_thickness * 2

    @property
    def room_unit_height(self):
        return self.room_tile_height + self.wall_thickness * 2

    def connect_adjacent_rooms(self):
        for (gx, gy), room in list(self.rooms.items()):
            for dx, dy, direction in [(-1, 0, "west"), (1, 0, "east"),
                                      (0, -1, "north"), (0, 1, "south")]:
                nx, ny = gx + dx, gy + dy
                if (nx, ny) in self.rooms and not room.has_door(direction):
                    room.connect_to(self.rooms[(nx, ny)], direction)

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
                return (
                    room_start_x + room_tile_width // 2,
                    room_start_y + room_tile_height // 2,
                )
        return 3, 2

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
        room_unit_width = self.room_tile_width + self.wall_thickness * 2
        room_unit_height = self.room_tile_height + self.wall_thickness * 2
        room_x = tile_x // room_unit_width
        room_y = tile_y // room_unit_height
        return (room_x, room_y)

    def get_current_room(self, tile_x, tile_y):
        room_coord = self.get_room_at(tile_x, tile_y)
        return self.rooms.get(room_coord)
