from map.tilemap import Block, Ground, Decoration, Bed, Wardrobe, DungeonEntrance


class SpriteFactory:
    def __init__(self, game):
        self.game = game

    def build_tile_sprites(self, level, room_start_x, room_start_y, room_end_x, room_end_y):
        for i, row in enumerate(level):
            if i < room_start_y or i >= room_end_y:
                continue
            for j, column in enumerate(row):
                if j < room_start_x or j >= room_end_x:
                    continue
                if column == " ":
                    Ground(self.game, j, i, " ")
                else:
                    Ground(self.game, j, i)
                if column == "B":
                    Block(self.game, j, i)
                elif column == "T":
                    Decoration(self.game, j, i, "tree")
                elif column == "H":
                    Bed(self.game, j, i)
                elif column == "W":
                    Wardrobe(self.game, j, i)

    def build_void_margin(self, level, room_start_x, room_start_y, room_end_x, room_end_y,
                          map_width, map_height, margin=1):
        void_start_x = max(0, room_start_x - margin)
        void_end_x = min(map_width, room_end_x + margin)
        void_start_y = max(0, room_start_y - margin)
        void_end_y = min(map_height, room_end_y + margin)

        for i in range(void_start_y, void_end_y):
            for j in range(void_start_x, void_end_x):
                if room_start_y <= i < room_end_y and room_start_x <= j < room_end_x:
                    continue
                if level[i][j] == " ":
                    Ground(self.game, j, i, " ")

    def build_portal(self, gx, gy, boss_pos):
        if boss_pos:
            portal = DungeonEntrance(self.game, boss_pos[0], boss_pos[1])
            portal.room_coord = (gx, gy)
            return portal
        return None
