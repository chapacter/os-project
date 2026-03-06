import random
from enum import Enum

import noise
import numpy as np


class Biome(Enum):
    WATER = "~"
    SAND = ":"
    GRASS = "."
    FOREST = "T"
    MOUNTAIN = "B"
    SWAMP = "S"
    LAVA = "L"


BIOME_THRESHOLDS = {
    "water": 0.25,
    "sand": 0.35,
    "grass": 0.55,
    "forest": 0.70,
    "mountain": 0.80,
}


class WorldGenerator:
    def __init__(self, world_width, world_height, seed=None):
        self.world_width = world_width
        self.world_height = world_height
        self.seed = seed if seed is not None else random.randint(0, 1000000)
        random.seed(self.seed)
        np.random.seed(self.seed)

        self.scale = 20
        self.octaves = 4
        self.persistence = 0.5
        self.lacunarity = 2.0

        self.biome_count = 6
        self.dungeon_entrances = []

    def noise2d(self, x, y):
        return noise.pnoise2(
            x / self.scale,
            y / self.scale,
            octaves=self.octaves,
            persistence=self.persistence,
            lacunarity=self.lacunarity,
            base=self.seed,
        )

    def get_biome(self, value):
        normalized = (value + 1) / 2

        if normalized < BIOME_THRESHOLDS["water"]:
            return Biome.WATER
        elif normalized < BIOME_THRESHOLDS["sand"]:
            return Biome.SAND
        elif normalized < BIOME_THRESHOLDS["grass"]:
            return Biome.GRASS
        elif normalized < BIOME_THRESHOLDS["forest"]:
            return Biome.FOREST
        elif normalized < BIOME_THRESHOLDS["mountain"]:
            return Biome.MOUNTAIN
        else:
            return Biome.LAVA

    def generate_zone(self, zone_x, zone_y):
        zone_width = self.world_width
        zone_height = self.world_height
        zone_data = []

        for y in range(zone_height):
            row = []
            for x in range(zone_width):
                world_x = zone_x * zone_width + x
                world_y = zone_y * zone_height + y

                noise_val = self.noise2d(world_x, world_y)
                biome = self.get_biome(noise_val)
                tile = biome.value

                if biome in [Biome.GRASS, Biome.FOREST, Biome.MOUNTAIN]:
                    if random.random() < 0.05:
                        tile = "E"

                row.append(tile)
            zone_data.append(row)

        return zone_data

    def generate_world(self):
        world = {}
        center_x, center_y = 0, 0

        for zy in range(-1, 2):
            for zx in range(-1, 2):
                zone_data = self.generate_zone(zx, zy)

                if zx == center_x and zy == center_y:
                    zone_data = self.add_village(zone_data)
                else:
                    if random.random() < 0.4:
                        self.add_dungeon_entrance(zone_data, zx, zy)

                world[(zx, zy)] = zone_data

        return world

    def pregenerate_all_zones(self):
        return self.generate_world()

    def add_village(self, zone_data):
        village_width = 8
        village_height = 8
        start_x = len(zone_data[0]) // 2 - village_width // 2
        start_y = len(zone_data) // 2 - village_height // 2

        for y in range(start_y, start_y + village_height):
            for x in range(start_x, start_x + village_width):
                if 0 <= y < len(zone_data) and 0 <= x < len(zone_data[0]):
                    zone_data[y][x] = "V"

        houses = []
        for _ in range(random.randint(3, 6)):
            house_x = start_x + random.randint(1, village_width - 2)
            house_y = start_y + random.randint(1, village_height - 2)
            if 0 <= house_y < len(zone_data) and 0 <= house_x < len(zone_data[0]):
                zone_data[house_y][house_x] = "H"
                houses.append((house_y, house_x))

        if 0 <= start_y + village_height // 2 < len(zone_data):
            p_x = start_x + village_width // 2
            p_y = start_y + village_height // 2
            zone_data[p_y][p_x] = "P"

        npc_count = random.randint(3, 5)
        for _ in range(npc_count):
            npc_x = start_x + random.randint(1, village_width - 2)
            npc_y = start_y + random.randint(1, village_height - 2)
            if (
                    0 <= npc_y < len(zone_data)
                    and 0 <= npc_x < len(zone_data[0])
                    and zone_data[npc_y][npc_x] not in ["H", "P"]
            ):
                zone_data[npc_y][npc_x] = "N"

        return zone_data

    def add_dungeon_entrance(self, zone_data, zone_x, zone_y):
        entrance_x = random.randint(2, len(zone_data[0]) - 3)
        entrance_y = random.randint(2, len(zone_data) - 3)

        if zone_data[entrance_y][entrance_x] in [".", ":", "T"]:
            zone_data[entrance_y][entrance_x] = "D"
            self.dungeon_entrances.append((zone_x, zone_y, entrance_x, entrance_y))

    def get_zone_at(self, zone_x, zone_y):
        return self.generate_zone(zone_x, zone_y)
