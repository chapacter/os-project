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

    def __repr__(self):
        return f"Room({self.x}, {self.y}, {self.room_type.value})"
