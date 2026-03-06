import random
from enum import Enum


class RoomType(Enum):
    START = "start"
    EMPTY = "empty"
    ENEMY = "enemy"
    ELITE = "elite"
    LOOT = "loot"
    BOSS = "boss"
    EXIT = "exit"


class Room:
    def __init__(self, x, y, room_type=RoomType.EMPTY):
        self.x = x
        self.y = y
        self.room_type = room_type
        self.doors = {"north": False, "south": False, "east": False, "west": False}
        self.width = random.randint(3, 5)
        self.height = random.randint(3, 5)
        self.visited = False
        self.visible = False
        self.enemy_count = 0
        self.enemies_spawned = False

    def has_door(self, direction):
        return self.doors.get(direction, False)

    def set_door(self, direction, value=True):
        if direction in self.doors:
            self.doors[direction] = value

    def connect_to(self, other, direction):
        self.set_door(direction, True)
        opposite = {"north": "south", "south": "north", "east": "west", "west": "east"}
        other.set_door(opposite[direction], True)

    def is_passable(self):
        return any(self.doors.values())

    def set_visible(self, value=True):
        self.visible = value

    def set_visited(self, value=True):
        self.visited = value

    def get_neighbor_coords(self, direction):
        if direction == "north":
            return (self.x, self.y - 1)
        elif direction == "south":
            return (self.x, self.y + 1)
        elif direction == "east":
            return (self.x + 1, self.y)
        elif direction == "west":
            return (self.x - 1, self.y)
        return None

    def __repr__(self):
        return f"Room({self.x}, {self.y}, {self.room_type.value}, visible={self.visible}, visited={self.visited})"
