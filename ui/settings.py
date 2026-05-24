import pygame

from ui.font_manager import font_manager
from utils.audio import audio_manager
from utils.config import set_menu_music_volume, set_dungeon_music_volume, set_sfx_volume
from utils.settings import WHITE, BLACK, YELLOW

SLIDER_TRACK = (50, 50, 50)
SLIDER_FILL = (100, 180, 255)
SLIDER_BORDER = (180, 180, 180)
SLIDER_FOCUS = (255, 215, 0)
HANDLE_COLOR = (255, 255, 255)

STEP_RATIO = 0.01


class SettingsMenu:
    def __init__(self, game):
        self.game = game
        self.is_active = False

        self.background = pygame.image.load("assets/menu1.jpg").convert()
        self.background = pygame.transform.scale(self.background, game.sc.get_size())
        overlay = pygame.Surface(game.sc.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        self.background.blit(overlay, (0, 0))

        self.slider_width = 350
        self.slider_height = 16
        self.track_height = 16

        self.sliders = []
        self.focused_index = 0
        self.dragging = False
        self.drag_index = -1

        self.back_rect = pygame.Rect(0, 0, 220, 50)

    def _build_sliders(self):
        cx = self.game.sc.get_width() // 2
        cy = self.game.sc.get_height() // 2

        self.sliders = [
            {
                "label_key": "settings.menu_music_volume",
                "getter": lambda: audio_manager.menu_music_volume,
                "setter": lambda v: (
                    audio_manager.set_menu_music_volume(v),
                    set_menu_music_volume(v),
                ),
                "rect": pygame.Rect(cx - self.slider_width // 2, cy - 40, self.slider_width, self.track_height),
                "label_y": cy - 70,
                "value": audio_manager.menu_music_volume,
                "max_val": 1.0,
            },
            {
                "label_key": "settings.dungeon_music_volume",
                "getter": lambda: audio_manager.dungeon_music_volume,
                "setter": lambda v: (
                    audio_manager.set_dungeon_music_volume(v),
                    set_dungeon_music_volume(v),
                ),
                "rect": pygame.Rect(cx - self.slider_width // 2, cy + 20, self.slider_width, self.track_height),
                "label_y": cy - 10,
                "value": audio_manager.dungeon_music_volume,
                "max_val": 1.0,
            },
            {
                "label_key": "settings.sfx_volume",
                "getter": lambda: audio_manager.sfx_volume,
                "setter": lambda v: (
                    audio_manager.set_sfx_volume(v),
                    set_sfx_volume(v),
                ),
                "rect": pygame.Rect(cx - self.slider_width // 2, cy + 80, self.slider_width, self.track_height),
                "label_y": cy + 50,
                "value": audio_manager.sfx_volume,
                "max_val": 2.0,
            },
        ]

        for s in self.sliders:
            s["value"] = s["getter"]()

        self.back_rect = pygame.Rect(cx - 110, cy + 150, 220, 50)

    def _update_slider_value(self, index, val):
        s = self.sliders[index]
        val = max(0.0, min(s["max_val"], round(val, 2)))
        s["value"] = val
        s["setter"](val)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            for i, s in enumerate(self.sliders):
                if s["rect"].collidepoint(pos):
                    self.focused_index = i
                    self.dragging = True
                    self.drag_index = i
                    ratio = (pos[0] - s["rect"].left) / s["rect"].width
                    self._update_slider_value(i, ratio * s["max_val"])
                    audio_manager.play_sound("menu_move")
                    return
            if self.back_rect.collidepoint(pos):
                audio_manager.play_sound("menu_select")
                self.game.settings_back()
                return

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
            self.drag_index = -1

        elif event.type == pygame.MOUSEMOTION and self.dragging and self.drag_index >= 0:
            s = self.sliders[self.drag_index]
            pos = event.pos
            ratio = (pos[0] - s["rect"].left) / s["rect"].width
            self._update_slider_value(self.drag_index, ratio * s["max_val"])
        elif event.type == pygame.MOUSEMOTION and not self.dragging:
            prev = self.focused_index
            for i, s in enumerate(self.sliders):
                if s["rect"].collidepoint(event.pos):
                    self.focused_index = i
                    if prev != self.focused_index:
                        audio_manager.play_sound("menu_move")
                    return
            if self.back_rect.collidepoint(event.pos):
                self.focused_index = len(self.sliders)
                if prev != self.focused_index:
                    audio_manager.play_sound("menu_move")

        elif event.type == pygame.MOUSEWHEEL:
            if 0 <= self.focused_index < len(self.sliders):
                s = self.sliders[self.focused_index]
                delta = event.y * s["max_val"] * STEP_RATIO
                self._update_slider_value(self.focused_index, s["value"] + delta)

        elif event.type == pygame.KEYDOWN:
            total = len(self.sliders) + 1
            prev = self.focused_index
            if event.key in (pygame.K_w, pygame.K_UP):
                self.focused_index = (self.focused_index - 1) % total
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self.focused_index = (self.focused_index + 1) % total
            elif event.key in (pygame.K_a, pygame.K_LEFT):
                if 0 <= self.focused_index < len(self.sliders):
                    s = self.sliders[self.focused_index]
                    self._update_slider_value(self.focused_index, s["value"] - s["max_val"] * STEP_RATIO)
            elif event.key in (pygame.K_d, pygame.K_RIGHT):
                if 0 <= self.focused_index < len(self.sliders):
                    s = self.sliders[self.focused_index]
                    self._update_slider_value(self.focused_index, s["value"] + s["max_val"] * STEP_RATIO)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.focused_index >= len(self.sliders):
                    audio_manager.play_sound("menu_select")
                    self.game.settings_back()
                    return
            if prev != self.focused_index:
                audio_manager.play_sound("menu_move")

    def update(self, time_delta):
        pass

    def draw(self, surface):
        surface.blit(self.background, (0, 0))

        cx = self.game.sc.get_width() // 2
        cy = self.game.sc.get_height() // 2

        panel = pygame.Rect(cx - 280, cy - 180, 560, 400)
        pygame.draw.rect(surface, (25, 25, 40), panel)
        pygame.draw.rect(surface, SLIDER_BORDER, panel, 2)

        title_surf = font_manager.render(
            font_manager.t("settings.title"), 36, WHITE, shadow=BLACK
        )
        title_rect = title_surf.get_rect(center=(cx, cy - 130))
        surface.blit(title_surf, title_rect)

        for i, s in enumerate(self.sliders):
            focused = i == self.focused_index
            self._draw_slider(surface, s, focused)

        back_focused = self.focused_index >= len(self.sliders)
        self._draw_back_button(surface, back_focused)

    def _draw_slider(self, surface, s, focused):
        cx = self.game.sc.get_width() // 2
        label_surf = font_manager.render(font_manager.t(s["label_key"]), 22, WHITE, shadow=BLACK)
        label_rect = label_surf.get_rect(center=(cx, s["label_y"]))
        surface.blit(label_surf, label_rect)

        rect = s["rect"]
        ratio = min(1.0, s["value"] / s["max_val"])

        pygame.draw.rect(surface, SLIDER_TRACK, rect)

        fill_w = int(rect.width * ratio)
        if fill_w > 0:
            fill_rect = pygame.Rect(rect.left, rect.top, fill_w, rect.height)
            pygame.draw.rect(surface, SLIDER_FILL, fill_rect)

        border = SLIDER_FOCUS if focused else SLIDER_BORDER
        pygame.draw.rect(surface, border, rect, 2)

        handle_x = rect.left + fill_w
        handle_rect = pygame.Rect(handle_x - 3, rect.top - 3, 6, rect.height + 6)
        pygame.draw.rect(surface, HANDLE_COLOR, handle_rect)

        pct = int(s["value"] / s["max_val"] * 100)
        pct_surf = font_manager.render(f"{pct}%", 18, WHITE, shadow=BLACK)
        pct_rect = pct_surf.get_rect(midleft=(rect.right + 10, rect.centery))
        surface.blit(pct_surf, pct_rect)

    def _draw_back_button(self, surface, focused):
        color = SLIDER_FOCUS if focused else YELLOW
        pygame.draw.rect(surface, color, self.back_rect, 2)

        text = font_manager.t("settings.back")
        text_surf = font_manager.render(text, 24, color, shadow=BLACK)
        text_rect = text_surf.get_rect(center=self.back_rect.center)
        surface.blit(text_surf, text_rect)

    def show(self):
        self.is_active = True
        self.focused_index = 0
        self._build_sliders()

    def hide(self):
        self.is_active = False
        self.sliders.clear()
