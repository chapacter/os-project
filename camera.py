import pygame
from settings import *


class Camera:
    def __init__(self, screen_width, screen_height, map_width=None, map_height=None):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.map_width = map_width or (WIN_WIDTH * 2)
        self.map_height = map_height or (WIN_HEIGHT * 2)

        self.scroll_x = 0
        self.scroll_y = 0

        self.parallax_layers = []

    def set_map_size(self, map_width, map_height):
        self.map_width = map_width
        self.map_height = map_height

    def apply(self, sprite):
        if hasattr(sprite, "rect"):
            return sprite.rect.copy()
        return pygame.Rect(0, 0, 0, 0)

    def apply_rect(self, rect):
        new_rect = rect.copy()
        new_rect.x -= self.scroll_x
        new_rect.y -= self.scroll_y
        return new_rect

    def apply_pos(self, pos):
        return pos[0] - self.scroll_x, pos[1] - self.scroll_y

    def center_on(self, x, y):
        camera_x = x - self.screen_width // 2
        camera_y = y - self.screen_height // 2

        camera_x = max(0, min(camera_x, self.map_width - self.screen_width))
        camera_y = max(0, min(camera_y, self.map_height - self.screen_height))

        self.scroll_x = camera_x
        self.scroll_y = camera_y

    def follow_sprite(self, sprite):
        if sprite and hasattr(sprite, "rect"):
            self.center_on(sprite.rect.centerx, sprite.rect.centery)

    def move(self, dx, dy):
        self.scroll_x += dx
        self.scroll_y += dy

    def shake(self, intensity=5, duration=0.2):
        import random

        self._shake_intensity = intensity
        self._shake_duration = duration
        self._shake_timer = 0
        self._shake_original_x = self.scroll_x
        self._shake_original_y = self.scroll_y

    def update(self, dt):
        if hasattr(self, "_shake_timer") and self._shake_timer < self._shake_duration:
            import random

            self._shake_timer += dt
            dx = random.randint(-self._shake_intensity, self._shake_intensity)
            dy = random.randint(-self._shake_intensity, self._shake_intensity)
            self.scroll_x = self._shake_original_x + dx
            self.scroll_y = self._shake_original_y + dy
        elif hasattr(self, "_shake_timer"):
            self.scroll_x = self._shake_original_x
            self.scroll_y = self._shake_original_y

    def add_parallax_layer(self, image, speed=0.5, y_offset=0):
        layer = {"image": image, "speed": speed, "y_offset": y_offset}
        self.parallax_layers.append(layer)

    def draw_parallax(self, surface):
        for layer in self.parallax_layers:
            parallax_x = (
                    int(self.scroll_x * layer["speed"]) % layer["image"].get_width()
            )
            parallax_y = int(self.scroll_y * layer["speed"]) + layer["y_offset"]

            surface.blit(layer["image"], (-parallax_x, -parallax_y))

            if parallax_x > 0:
                surface.blit(
                    layer["image"],
                    (layer["image"].get_width() - parallax_x, -parallax_y),
                )

    def get_view_rect(self):
        return pygame.Rect(
            self.scroll_x, self.scroll_y, self.screen_width, self.screen_height
        )

    def to_world(self, screen_pos):
        return screen_pos[0] + self.scroll_x, screen_pos[1] + self.scroll_y

    def to_screen(self, world_pos):
        return world_pos[0] - self.scroll_x, world_pos[1] - self.scroll_y


class CameraGroup(pygame.sprite.LayeredUpdates):
    def __init__(self, camera, *sprites):
        super().__init__(*sprites)
        self.camera = camera

    def draw(self, surface):
        for sprite in self.sprites():
            if hasattr(sprite, "image") and hasattr(sprite, "rect"):
                offset_rect = self.camera.apply_rect(sprite.rect)
                surface.blit(sprite.image, offset_rect)
