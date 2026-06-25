import random

from map.dungeon_generator_old_graph import _DungeonGraphMixin


class DungeonGeneratorOld(_DungeonGraphMixin):
    def __init__(self, grid_width=8, grid_height=8, seed=None):
        super().__init__(grid_width, grid_height, seed)

    def generate_floor(self, floor_number):
        self.floor_number = floor_number
        random.seed(self.seed + floor_number)

        self._graph = self._build_graph()
        self._graph.create_rooms()
        self._graph.connect_rooms()
        self._graph.assign_room_types()

        self.grid_width = self._graph.grid_width
        self.grid_height = self._graph.grid_height
        self.rooms = self._graph.rooms
        self.room_tile_width = self._graph.room_tile_width
        self.room_tile_height = self._graph.room_tile_height
        self.wall_thickness = self._graph.wall_thickness
        self.door_width = self._graph.door_width

        tile_map = self._tiler.generate()

        self.map_width = self._graph.map_width
        self.map_height = self._graph.map_height

        return tile_map

    def pregenerate_all_floors(self, num_floors=4):
        floors = {}
        for floor in range(1, num_floors + 1):
            floors[floor] = self.generate_floor(floor)
        return floors
