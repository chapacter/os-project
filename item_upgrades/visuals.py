import math

import pygame

from utils.settings import LOOT_FLY_DURATION


class UpgradeVisual(pygame.sprite.Sprite):
    def __init__(self, game, x, y, upgrade_type, ecs_world):
        self.game = game
        self.x = x
        self.y = y
        self.render_mode = "orthogonal"
        self.upgrade_type = upgrade_type
        self.width = 32
        self.height = 32

        # Create placeholder icon
        self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self._draw_icon()
        self.image.set_alpha(128)

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self._layer = 4
        self.groups = game.all_sprites, game.items

        pygame.sprite.Sprite.__init__(self, self.groups)

        self._base_image = self.image.copy()
        self._cache_key = id(self._base_image)
        self._ensure_cache(self._base_image, self._cache_key)

        self.state = "flying"
        self.fly_timer = 0

    def _draw_icon(self):
        w, h = self.image.get_size()
        center_x, center_y = w // 2, h // 2
        size = min(w, h) // 3

        colors = {
            "damage": (100, 255, 100),
            "speed": (255, 200, 100),
            "knockback": (200, 200, 100),
            "pierce": (150, 100, 255),
            "area": (255, 100, 200),
            "explosion": (255, 255, 100),
            "boomerang": (100, 255, 255),
            "double_attack": (255, 150, 100),
            "cone_attack": (255, 200, 255),
        }
        color = colors.get(self.upgrade_type, (100, 200, 100))

        center_angle = 45
        radius = min(w, h) // 3
        points = []
        count = 5
        for i in range(count):
            angle = math.radians(center_angle + i * 2 * math.pi / count)
            px = center_x + radius * math.cos(angle)
            py = center_y + radius * math.sin(angle)
            points.append((px, py))
        points.append(points[0])

        pygame.draw.polygon(self.image, color, points)

    def _ensure_cache(self, base_surface, cache_key):
        if cache_key in self._rotation_cache:
            return

        angles = range(0, self._rotation_max_angle + 1, self._rotation_step)
        cache = []
        for angle in angles:
            transformed = self._transform_perspective(base_surface, angle)
            cache.append(transformed)

        self._rotation_cache[cache_key] = cache

    def _transform_perspective(self, surface, angle_deg):
        w, h = surface.get_size()
        if w == 0 or h == 0:
            return surface

        scale = max(0.15, abs(math.cos(math.radians(angle_deg))))
        new_w = max(1, int(w * scale))
        return pygame.transform.scale(surface, (new_w, h))

    def _get_parabola_pos(self, t):
        one_minus_t = 1 - t
        return (
                one_minus_t * one_minus_t * self.start_pos
                + 2 * one_minus_t * t * self.apex_pos
                + t * t * self.end_pos
        )

    def _init_flight(self):
        distance = random.randint(20, 50)
        direction = random.choice([(-1, 1), (1, 1), (1, -1), (-1, -1)])
        self.start_pos = pygame.math.Vector2(self.rect.x, self.rect.y)
        self.end_pos = pygame.math.Vector2(
            self.start_pos.x + direction[0] * distance,
            self.start_pos.y + direction[1] * distance,
        )
        self.apex_pos = pygame.math.Vector2(
            (self.start_pos.x + self.end_pos.x) / 2,
            (self.start_pos.y + self.end_pos.y) / 2 - 10,
        )
        self.state = "flying"
        self.fly_timer = 0

    def animate(self):
        self.rotation_angle += self._rotation_step * self._rotation_direction
        if self.rotation_angle >= self._rotation_max_angle:
            self.rotation_angle = self._rotation_max_angle
            self._rotation_direction = -1
        elif self.rotation_angle <= 0:
            self.rotation_angle = 0
            self._rotation_direction = 1

        cache_index = self.rotation_angle // self._rotation_step
        if self._cache_key in self._rotation_cache:
            frames = self._rotation_cache[self._cache_key]
            if 0 <= cache_index < len(frames):
                self.image = frames[cache_index]
                self.rect = self.image.get_rect(center=self.rect.center)

    def update(self):
        if self.state == "flying":
            self.fly_timer += 1
            t = self.fly_timer / LOOT_FLY_DURATION
            pos = self._get_parabola_pos(t)
            self.rect.x = pos.x
            self.rect.y = pos.y

            if self.fly_timer >= LOOT_FLY_DURATION:
                self.state = "landed"
                self.rect.x = self.end_pos.x
                self.rect.y = self.end_pos.y

        self.animate()

    def on_pickup(self, player):
        self.game.services.audio.play_sound("menu_select")
        self.kill()
        return True
