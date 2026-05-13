import pygame

from map.room import RoomType
from ui.font_manager import font_manager
from utils.settings import WHITE, BLACK, YELLOW

ROOM_COLORS = {
    RoomType.LOBBY: (0, 200, 0),
    RoomType.ENEMY: (255, 165, 0),
    RoomType.ELITE: (200, 50, 50),
    RoomType.LOOT: (255, 215, 0),
    RoomType.BOSS: (180, 0, 180),
    RoomType.EVENT: (0, 200, 200),
}

ROOM_LABELS = {
    RoomType.LOBBY: "LOBBY",
    RoomType.ENEMY: "ENEMY",
    RoomType.ELITE: "ELITE",
    RoomType.LOOT: "LOOT",
    RoomType.BOSS: "BOSS",
    RoomType.EVENT: "EVENT",
}


class DungeonMap:
    def __init__(self, game):
        self.game = game
        self.visible = False
        self.cell_size = 80
        self.padding = 30

    def toggle(self):
        self.visible = not self.visible

    def draw(self, surface):
        if not self.visible or self.game.mode != "dungeon":
            return

        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        w, h = surface.get_size()
        rooms = self.game.dungeon_generator.rooms
        if not rooms:
            return

        min_gx = min(r.x for r in rooms.values())
        max_gx = max(r.x for r in rooms.values())
        min_gy = min(r.y for r in rooms.values())
        max_gy = max(r.y for r in rooms.values())

        grid_w = max_gx - min_gx + 1
        grid_h = max_gy - min_gy + 1

        map_w = grid_w * self.cell_size
        map_h = grid_h * self.cell_size
        offset_x = (w - map_w) // 2
        offset_y = (h - map_h) // 2 - 20

        floor = self.game.current_dungeon_floor
        title = font_manager.render(f"Floor {floor}", 32, WHITE, shadow=BLACK)
        title_rect = title.get_rect(center=(w // 2, offset_y - 30))
        surface.blit(title, title_rect)

        player_room_coord = None
        if hasattr(self.game, "player") and self.game.player:
            player_tile_x = int(self.game.player.rect.x / 32)
            player_tile_y = int(self.game.player.rect.y / 32)
            player_room_coord = self.game.dungeon_generator.get_room_at(
                player_tile_x, player_tile_y
            )

        for coord, room in rooms.items():
            gx, gy = coord
            cx = offset_x + (gx - min_gx) * self.cell_size
            cy = offset_y + (gy - min_gy) * self.cell_size
            rect = pygame.Rect(cx + 2, cy + 2, self.cell_size - 4, self.cell_size - 4)

            color = ROOM_COLORS.get(room.room_type, (80, 80, 80))
            if not room.visited:
                color = tuple(c // 3 for c in color)

            pygame.draw.rect(surface, color, rect, border_radius=4)
            pygame.draw.rect(surface, WHITE, rect, 1, border_radius=4)

            if coord == player_room_coord:
                pygame.draw.rect(surface, YELLOW, rect, 3, border_radius=4)

            label = ROOM_LABELS.get(room.room_type, "")
            if label:
                label_surf = font_manager.render(label, 16, WHITE, shadow=BLACK)
                label_rect = label_surf.get_rect(center=rect.center)
                surface.blit(label_surf, label_rect)

        # Legend on the right-bottom of the map
        legend_x = offset_x + map_w + 10
        legend_h = len(ROOM_COLORS) * 25
        legend_y_start = offset_y + map_h - legend_h

        # Keep legend inside screen bounds
        if legend_x + 120 > w:
            legend_x = offset_x - 120

        for i, (rtype, color) in enumerate(ROOM_COLORS.items()):
            ly = legend_y_start + i * 25
            pygame.draw.rect(surface, color, (legend_x, ly, 14, 14))
            lbl = font_manager.render(ROOM_LABELS[rtype], 14, WHITE, shadow=BLACK)
            surface.blit(lbl, (legend_x + 20, ly - 2))

        hint = font_manager.render("[M] \u0417\u0430\u043a\u0440\u044b\u0442\u044c", 16, WHITE, shadow=BLACK)
        hint_rect = hint.get_rect(center=(w // 2, h - 20))
        surface.blit(hint, hint_rect)
