class DoorLayoutCalculator:
    def __init__(self, graph):
        self.graph = graph

    def calculate(self):
        g = self.graph
        room_unit_width = g.room_unit_width
        room_unit_height = g.room_unit_height
        room_tile_width = g.room_tile_width
        room_tile_height = g.room_tile_height
        wall_thickness = g.wall_thickness
        door_width = g.door_width

        doors = []
        for (gx, gy), room in g.rooms.items():
            for door_dir, has_door in room.doors.items():
                if has_door:
                    room_start_x = gx * room_unit_width + wall_thickness
                    room_start_y = gy * room_unit_height + wall_thickness
                    room_end_x = room_start_x + room_tile_width
                    room_end_y = room_start_y + room_tile_height

                    door_offset_x = room_tile_width // 2 - door_width // 2
                    door_offset_y = room_tile_height // 2 - door_width // 2

                    if door_dir == "north":
                        x = room_start_x + door_offset_x
                        y = room_start_y - 1
                        to_room = (gx, gy - 1)
                    elif door_dir == "south":
                        x = room_start_x + door_offset_x
                        y = room_end_y
                        to_room = (gx, gy + 1)
                    elif door_dir == "east":
                        x = room_end_x
                        y = room_start_y + door_offset_y
                        to_room = (gx + 1, gy)
                    elif door_dir == "west":
                        x = room_start_x - 1
                        y = room_start_y + door_offset_y
                        to_room = (gx - 1, gy)
                    else:
                        continue

                    if to_room in g.rooms:
                        doors.append({
                            "x": x,
                            "y": y,
                            "direction": door_dir,
                            "from_room": (gx, gy),
                            "to_room": to_room,
                        })
        return doors
