import noise


class NoiseGenerator:
    def __init__(self, seed, scale=20, octaves=4, persistence=0.5, lacunarity=2.0):
        self.seed = seed
        self.scale = scale
        self.octaves = octaves
        self.persistence = persistence
        self.lacunarity = lacunarity

    def noise2d(self, x, y):
        return noise.pnoise2(
            x / self.scale,
            y / self.scale,
            octaves=self.octaves,
            persistence=self.persistence,
            lacunarity=self.lacunarity,
            base=self.seed,
        )
