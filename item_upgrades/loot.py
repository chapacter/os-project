import math
import os
import random

import pygame

from entity.components.tags import LootMarker
from entity.ecs_helpers import ecs_register
from items.base import Item
from utils.settings import LOOT_FLY_DURATION, WEAPON_LAYER


class WeaponUpgradeLoot(Item):
    """Weapon upgrade loot that drops from enemies and bosses."""

    def __init__(self, game, x, y, weapon_stats):
        """Initialize weapon upgrade item.

        Args:
            game: Game reference
            x: Tile x position
            y: Tile y position
            weapon_stats: Dictionary
        """
        self.game = game
        self.image = None
        self.x = x
        self.y = y
        self.width = 128 // 8
        self.height = 48 // 3

        stats = weapon_stats['stats']
        self.weapon_type = weapon_stats.get('type', weapon_stats.get('effect_type', 'normal'))
        self.stats = stats
        self.current_level = weapon_stats.get('level', 1)
        self.max_level = weapon_stats.get('max_level', 3)
        effect_type = stats.get('effect_type', self.weapon_type)

        sprite_path = os.path.join("assets", "hallowicons_1.png")
        if os.path.exists(sprite_path):
            full_image = pygame.image.load(sprite_path).convert_alpha()
            tile_w = full_image.get_width() // 8
            tile_h = full_image.get_height() // 3
            row = 2
            col = weapon_stats.get('col', 0)
            src_x = col * tile_w
            src_y = row * tile_h
            self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            tile = pygame.Surface((tile_w, tile_h), pygame.SRCALPHA)
            try:
                tile.blit(full_image, (0, 0), (src_x, src_y, tile_w, tile_h))
            except:
                pass
            self.image = pygame.transform.scale(tile, (self.width, self.height))
        else:
            self.image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            self._draw_placeholder()

        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        self._layer = WEAPON_LAYER
        self.groups = game.all_sprites, game.items

        pygame.sprite.Sprite.__init__(self, self.groups)

        self._base_image = self.image.copy()
        self._cache_key = id(self._base_image)
        self._ensure_cache(self._base_image, self._cache_key)
        self.rotation_angle = 0
        self._rotation_direction = 1

        self.state = "flying"
        self.fly_timer = 0

        self._init_flight()
        self._init_animation()
        self._register_ecs()

    def _draw_placeholder(self):
        """Draw placeholder image for missing sprites."""
        w, h = self.image.get_size()
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        type_colors = {
            'sword': (100, 255, 100),
            'arrow': (255, 200, 100),
            'bomb': (200, 100, 100),
            'boomerang': (150, 255, 255),
        }
        color = type_colors.get(self.weapon_type, (100, 200, 100))

        center_x, center_y = w // 2, h // 2
        size = min(w, h) // 3
        radius = size // 2
        cx, cy = center_x - radius / 2, center_y - radius / 2

        if self.weapon_type == 'sword':
            pygame.draw.polygon(surf, color, [[cx + size, cy], [cx, cy + size / 2], [cx, cy]])
        elif self.weapon_type in ['arrow', 'bomb']:
            pygame.draw.ellipse(surf, color, (cx - size // 2, cy - size // 3, size, size * 4 / 3))
        elif self.weapon_type == 'boomerang':
            points = []
            count = 5
            for i in range(count):
                angle = math.radians(self.weapon_type if i == 0 else i * 2 * math.pi / count)
                px = cx + radius * math.cos(angle)
                py = cy + radius * math.sin(angle)
                points.append((px, py))
            points.append(points[0])
            pygame.draw.polygon(surf, color, points)
        else:
            pygame.draw.circle(surf, color, (cx, cy), radius)

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

    def _init_animation(self):
        self.rotation_angle = 0
        self._rotation_direction = 1

    def _register_ecs(self):
        if self.game and self.game.ecs_world:
            ecs_register(self.game.ecs_world, self, rect=self.rect, image=self.image)
            self.game.ecs_world.add_component(self, LootMarker())

    def _get_parabola_pos(self, t):
        one_minus_t = 1 - t
        return (
                one_minus_t * one_minus_t * self.start_pos
                + 2 * one_minus_t * t * self.apex_pos
                + t * t * self.end_pos
        )

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
