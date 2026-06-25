import random


class VillageGenerator:
    def add_village(self, zone_data):
        village_width = 8
        village_height = 8
        start_x = len(zone_data[0]) // 2 - village_width // 2
        start_y = len(zone_data) // 2 - village_height // 2

        for y in range(start_y, start_y + village_height):
            for x in range(start_x, start_x + village_width):
                if 0 <= y < len(zone_data) and 0 <= x < len(zone_data[0]):
                    zone_data[y][x] = "V"

        for _ in range(random.randint(3, 6)):
            house_x = start_x + random.randint(1, village_width - 2)
            house_y = start_y + random.randint(1, village_height - 2)
            if 0 <= house_y < len(zone_data) and 0 <= house_x < len(zone_data[0]):
                zone_data[house_y][house_x] = "H"

        p_x = start_x + village_width // 2
        p_y = start_y + village_height // 2
        if 0 <= p_y < len(zone_data):
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
