from enum import Enum


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


class BiomeMap:
    def get_biome(self, noise_value: float) -> Biome:
        normalized = (noise_value + 1) / 2

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
