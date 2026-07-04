import math
from abc import ABC, abstractmethod

import pygame


class PerspectiveConfig:
    def __init__(self, angle_deg: float = 0.0):
        self.angle_deg = angle_deg
        self.shear_tan = math.tan(math.radians(angle_deg))

    def set_angle(self, angle_deg: float):
        self.angle_deg = angle_deg
        self.shear_tan = math.tan(math.radians(angle_deg))


class PerspectiveTransformStrategy(ABC):
    @abstractmethod
    def transform_point(self, cx: float, cy: float, center_x: float) -> tuple[float, float, float]:
        ...

    @abstractmethod
    def transform_image(self, surface: pygame.Surface, cx: float, cy: float, center_x: float) -> tuple:
        ...

    @abstractmethod
    def inv_transform_point(self, sx: float, sy: float, center_x: float) -> tuple[float, float]:
        ...


class ShearScaleStrategy(PerspectiveTransformStrategy):
    def __init__(self, config: PerspectiveConfig, screen_width: int, screen_height: int):
        self.config = config
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.world_anchor_delta = 0.0
        self._recalculate()

    def sync_config(self):
        self._recalculate()

    def _recalculate(self):
        self.k_perspective = self.config.shear_tan / max(self.screen_height, 1)

    def _anchor_cy(self, cy):
        return cy + self.world_anchor_delta

    def _screen_y(self, cy):
        wad = self.world_anchor_delta
        k = self.k_perspective
        return cy * (1.0 + k * wad) + k * cy * cy / 2.0

    def transform_point(self, cx: float, cy: float, center_x: float) -> tuple[float, float, float]:
        scale = 1.0 + self._anchor_cy(cy) * self.k_perspective
        if scale < 0.1:
            scale = 0.1
        sx = (cx - center_x) * scale + center_x
        sy = self._screen_y(cy)
        return sx, sy, scale

    def transform_image(self, surface: pygame.Surface, cx: float, cy: float, center_x: float) -> tuple:
        w, h = surface.get_size()
        k = self.k_perspective

        N = max(4, h // 4)
        strip_h = h / N

        sy_base_int = int(self._screen_y(cy))
        strip_ys = [0]
        for i in range(1, N):
            orig_y = i * strip_h
            strip_ys.append(int(self._screen_y(cy + orig_y)) - sy_base_int)
        strip_ys.append(int(self._screen_y(cy + h)) - sy_base_int)
        h_result = max(1, strip_ys[-1])

        strips = []
        for i in range(N):
            orig_y = i * strip_h
            orig_h = strip_h if i < N - 1 else h - orig_y

            s = 1.0 + self._anchor_cy(cy + orig_y + orig_h / 2) * k

            ix_left = math.floor((cx - center_x) * s + center_x)
            ix_right = math.floor((cx + w - center_x) * s + center_x)

            w_strip = max(1, ix_right - ix_left)
            h_strip = max(1, strip_ys[i + 1] - strip_ys[i])

            strips.append((w_strip, h_strip, ix_left, ix_right, int(orig_y), int(orig_h)))

        if not strips:
            return surface, 0, 0

        min_x = min(ixl for *_, ixl, _, _, _ in strips)
        max_x = max(ixr for *_, _, ixr, _, _ in strips)
        w_result = max(1, max_x - min_x)

        s_top = 1.0 + self._anchor_cy(cy) * k
        sx = (cx - center_x) * s_top + center_x
        dx = min_x - int(sx)

        result = pygame.Surface((w_result, h_result), pygame.SRCALPHA)
        y_pos = 0
        for w_strip, h_strip, ix_left, _, orig_y, orig_h in strips:
            x_in_result = ix_left - min_x
            src = pygame.Rect(0, orig_y, w, max(1, orig_h))
            sub = surface.subsurface(src)
            scaled = pygame.transform.scale(sub, (w_strip, h_strip))
            result.blit(scaled, (x_in_result, y_pos))
            y_pos += h_strip

        return result, dx, 0

    def inv_transform_point(self, sx: float, sy: float, center_x: float) -> tuple[float, float]:
        k = self.k_perspective
        wad = self.world_anchor_delta
        b = 1.0 + k * wad
        if abs(k) < 1e-10:
            cy = sy
        else:
            disc = b * b + 2.0 * k * sy
            if disc < 0.0:
                disc = 0.0
            cy = (-b + math.sqrt(disc)) / k
        scale = 1.0 + self._anchor_cy(cy) * k
        if abs(scale) < 0.001:
            scale = 0.001
        cx = (sx - center_x) / scale + center_x
        return cx, cy
