import random

import numpy as np

from map.biome_map import Biome, BiomeMap
from map.noise_generator import NoiseGenerator
from map.village_generator import VillageGenerator


class WorldGenerator:
    def __init__(self, world_width, world_height, seed=None, noise_gen=None, biome_map=None, village_gen=None):
        self.world_width = world_width
        self.world_height = world_height
        self.seed = seed if seed is not None else random.randint(0, 1000000)
        random.seed(self.seed)
        np.random.seed(self.seed)

        self.noise = noise_gen or NoiseGenerator(self.seed)
        self.biome_map = biome_map or BiomeMap()
        self.village_gen = village_gen or VillageGenerator()

        self.dungeon_entrances = []

    def generate_zone(self, zone_x, zone_y):
        zone_width = self.world_width
        zone_height = self.world_height
        zone_data = []

        for y in range(zone_height):
            row = []
            for x in range(zone_width):
                world_x = zone_x * zone_width + x
                world_y = zone_y * zone_height + y

                noise_val = self.noise.noise2d(world_x, world_y)
                biome = self.biome_map.get_biome(noise_val)
                tile = biome.value

                if biome in [Biome.GRASS, Biome.FOREST, Biome.MOUNTAIN]:
                    if random.random() < 0.05:
                        tile = "E"

                row.append(tile)
            zone_data.append(row)

        return zone_data

    def generate_world(self):
        world = {}

        for zy in range(-1, 2):
            for zx in range(-1, 2):
                zone_data = self.generate_zone(zx, zy)

                if zx == 0 and zy == 0:
                    zone_data = self.village_gen.add_village(zone_data)
                else:
                    if random.random() < 0.4:
                        self._add_dungeon_entrance(zone_data, zx, zy)

                world[(zx, zy)] = zone_data

        return world

    def pregenerate_all_zones(self):
        return self.generate_world()

    def _add_dungeon_entrance(self, zone_data, zone_x, zone_y):
        entrance_x = random.randint(2, len(zone_data[0]) - 3)
        entrance_y = random.randint(2, len(zone_data) - 3)

        if zone_data[entrance_y][entrance_x] in [".", ":", "T"]:
            zone_data[entrance_y][entrance_x] = "D"
            self.dungeon_entrances.append((zone_x, zone_y, entrance_x, entrance_y))

    def get_zone_at(self, zone_x, zone_y):
        return self.generate_zone(zone_x, zone_y)
