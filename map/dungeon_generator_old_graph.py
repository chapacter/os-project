import random

from map.factories.door_layout_calculator import DoorLayoutCalculator
from map.room_graph import RoomGraph
from map.room_tiler import RoomTiler


class _DungeonGraphMixin:
    def __init__(self, grid_width=8, grid_height=8, seed=None):
        self.seed = seed if seed is not None else random.randint(0, 1000000)
        random.seed(self.seed)

        self.grid_width = grid_width
        self.grid_height = grid_height
        self.rooms = {}
        self.floor_number = 1

        self.room_tile_width = 16
        self.room_tile_height = 16
        self.wall_thickness = 1
        self.door_width = 2

        self._map_width = 0
        self._map_height = 0
        self._graph = None
        self._tiler = None
        self._door_calculator = None

    @property
    def map_width(self):
        return self._map_width

    @map_width.setter
    def map_width(self, value):
        self._map_width = value

    @property
    def map_height(self):
        return self._map_height

    @map_height.setter
    def map_height(self, value):
        self._map_height = value

    def _build_graph(self):
        g = RoomGraph(self.grid_width, self.grid_height, self.seed)
        g.floor_number = self.floor_number
        self._tiler = RoomTiler(g)
        self._door_calculator = DoorLayoutCalculator(g)
        return g

    def get_room_size(self):
        return self.room_tile_width, self.room_tile_height

    def get_wall_thickness(self):
        return self.wall_thickness

    def get_door_width(self):
        return self.door_width

    def get_center_position(self):
        room_unit_width = self.room_tile_width + self.wall_thickness * 2
        room_unit_height = self.room_tile_height + self.wall_thickness * 2
        center_gx = self.grid_width // 2
        center_gy = self.grid_height // 2
        room_start_x = center_gx * room_unit_width + self.wall_thickness
        room_start_y = center_gy * room_unit_height + self.wall_thickness
        return room_start_x + self.room_tile_width // 2, room_start_y + self.room_tile_height // 2

    def get_start_position(self):
        return self._graph.get_start_position()

    def get_boss_position(self):
        return self._graph.get_boss_position()

    def get_event_position(self):
        return self._graph.get_event_position()

    def get_doors(self):
        return self._door_calculator.calculate()

    def set_start_room_visible(self):
        self._graph.set_start_room_visible()

    def set_room_visible(self, room_coord):
        self._graph.set_room_visible(room_coord)

    def get_room_at(self, tile_x, tile_y):
        return self._graph.get_room_at(tile_x, tile_y)

    def get_current_room(self, tile_x, tile_y):
        return self._graph.get_current_room(tile_x, tile_y)
