import pygame
import pytmx


class TiledMap:
    def __init__(self, game, filename):
        self.game = game
        self.filename = filename
        self.tmx_data = None
        self.width = 0
        self.height = 0
        self.tilewidth = 0
        self.tileheight = 0

        self.load()

    def load(self):
        try:
            self.tmx_data = pytmx.load_pygame(self.filename)
            self.width = self.tmx_data.width * self.tmx_data.tilewidth
            self.height = self.tmx_data.height * self.tmx_data.tileheight
            self.tilewidth = self.tmx_data.tilewidth
            self.tileheight = self.tmx_data.tileheight
        except Exception as e:
            print(f"Error loading TMX: {e}")
            self.tmx_data = None

    def render(self, surface):
        if not self.tmx_data:
            return

        for layer in self.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                for x, y, gid in layer:
                    tile = self.tmx_data.get_tile_image_by_gid(gid)
                    if tile:
                        surface.blit(tile, (x * self.tilewidth, y * self.tileheight))

    def make_map(self):
        if not self.tmx_data:
            return None

        temp_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.render(temp_surface)
        return temp_surface


class TiledLoader:
    def __init__(self, game):
        self.game = game
        self.maps = {}

    def load_map(self, filename):
        if filename in self.maps:
            return self.maps[filename]

        tmx_map = TiledMap(self.game, filename)
        self.maps[filename] = tmx_map
        return tmx_map

    def create_sprites_from_layer(self, tmx_map, layer_name, tile_type):
        if not tmx_map or not tmx_map.tmx_data:
            return []

        sprites = []

        for layer in tmx_map.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer) and layer.name == layer_name:
                for x, y, gid in layer:
                    if gid:
                        tile = tmx_map.tmx_data.get_tile_image_by_gid(gid)
                        if tile:
                            sprites.append(
                                {"x": x, "y": y, "image": tile, "type": tile_type}
                            )

        return sprites

    def create_sprites_from_object_group(self, tmx_map, group_name):
        if not tmx_map or not tmx_map.tmx_data:
            return []

        sprites = []

        for layer in tmx_map.tmx_data.visible_layers:
            if isinstance(layer, pytmx.TiledObjectGroup) and layer.name == group_name:
                for obj in layer:
                    sprites.append(
                        {
                            "name": obj.name,
                            "x": obj.x,
                            "y": obj.y,
                            "width": obj.width,
                            "height": obj.height,
                            "type": obj.type,
                            "properties": obj.properties,
                        }
                    )

        return sprites

    def load_tmx_to_sprites(self, filename, layer_mapping):
        tmx_map = self.load_map(filename)

        if not tmx_map or not tmx_map.tmx_data:
            return {}

        result = {"map": tmx_map, "tiles": {}, "objects": {}}

        for layer_name, tile_type in layer_mapping.items():
            tiles = self.create_sprites_from_layer(tmx_map, layer_name, tile_type)
            result["tiles"][layer_name] = tiles

        return result

    def get_map_size(self, filename):
        tmx_map = self.load_map(filename)
        if tmx_map:
            return tmx_map.width, tmx_map.height
        return 0, 0
