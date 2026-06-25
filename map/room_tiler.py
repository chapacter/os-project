import copy
import random

from map.models import RoomType


def _rotate_coord(x, y, rot, size=18):
    for _ in range(rot):
        x, y = y, size - 1 - x
    return x, y


SIDE_MAP = [
    {"north": "north", "south": "south", "east": "east", "west": "west"},
    {"north": "east", "south": "west", "east": "south", "west": "north"},
    {"north": "south", "south": "north", "east": "west", "west": "east"},
    {"north": "west", "south": "east", "east": "north", "west": "south"},
]


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


class RoomTiler:
    def __init__(self, graph):
        self.graph = graph

    def generate(self):
        g = self.graph
        room_tile_width = g.room_tile_width
        room_tile_height = g.room_tile_height
        wall_thickness = g.wall_thickness
        door_width = g.door_width

        room_unit_width = g.room_unit_width
        room_unit_height = g.room_unit_height

        total_width = g.grid_width * room_unit_width
        total_height = g.grid_height * room_unit_height

        tile_map = [["B" for _ in range(total_width)] for _ in range(total_height)]

        for (gx, gy), room in g.rooms.items():
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

        for (gx, gy), room in g.rooms.items():
            room_start_x = gx * room_unit_width + wall_thickness
            room_start_y = gy * room_unit_height + wall_thickness
            room_end_x = room_start_x + room_tile_width
            room_end_y = room_start_y + room_tile_height

            if room.has_door("north") and (gx, gy - 1) in g.rooms:
                for rx in range(door_width):
                    tx = room_start_x + (room_tile_width // 2 - door_width // 2) + rx
                    ty = room_start_y - 1
                    if 0 <= ty < total_height:
                        tile_map[ty][tx] = "."

            if room.has_door("south") and (gx, gy + 1) in g.rooms:
                for rx in range(door_width):
                    tx = room_start_x + (room_tile_width // 2 - door_width // 2) + rx
                    ty = room_end_y
                    if 0 <= ty < total_height:
                        tile_map[ty][tx] = "."

            if room.has_door("west") and (gx - 1, gy) in g.rooms:
                for ry in range(door_width):
                    tx = room_start_x - 1
                    ty = room_start_y + (room_tile_height // 2 - door_width // 2) + ry
                    if 0 <= tx < total_width:
                        tile_map[ty][tx] = "."

            if room.has_door("east") and (gx + 1, gy) in g.rooms:
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

        for (gx, gy), room in g.rooms.items():
            if room.room_type == RoomType.LOOT:
                room_start_x = gx * room_unit_width + wall_thickness
                room_start_y = gy * room_unit_height + wall_thickness
                cx = room_start_x + room_tile_width // 2
                cy = room_start_y + room_tile_height // 2
                if 0 <= cy < total_height and 0 <= cx < total_width:
                    tile_map[cy][cx] = "C"

        for (gx, gy), room in g.rooms.items():
            if room.room_type == RoomType.LOBBY:
                room_start_x = gx * room_unit_width + wall_thickness
                room_start_y = gy * room_unit_height + wall_thickness
                cx = room_start_x + room_tile_width // 2
                cy = room_start_y + room_tile_height // 2
                if 0 <= cy < total_height and 0 <= cx < total_width:
                    tile_map[cy][cx] = "H"

                wx = cx + 2
                wy = cy - 1
                if (0 <= wy < total_height and wy + 3 - 1 < total_height and
                        0 <= wx < total_width and wx + 3 - 1 < total_width):
                    tile_map[wy][wx] = "W"

        g.map_width = total_width
        g.map_height = total_height

        return tile_map

    def generate_from_templates(self, graph, room_instances, realm_id=None):
        g = graph
        room_tile_width = g.room_tile_width
        room_tile_height = g.room_tile_height
        rw = g.room_unit_width
        rh = g.room_unit_height

        total_width = g.grid_width * rw
        total_height = g.grid_height * rh

        tile_map = [["." for _ in range(total_width)] for _ in range(total_height)]

        for (gx, gy), room in g.rooms.items():
            instance = room_instances.get((gx, gy))
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

        for (gx, gy), room in g.rooms.items():
            room_start_x = gx * rw
            room_start_y = gy * rh

            if room_instances.get((gx, gy), {}).get("template"):
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

        g.map_width = total_width
        g.map_height = total_height

        return tile_map
