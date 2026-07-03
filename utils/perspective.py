import math
from abc import ABC, abstractmethod

import pygame


class PerspectiveConfig:
    def __init__(self, angle_deg: float = 15.0):
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
        self.shear_tan = config.shear_tan
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.k_perspective = config.shear_tan / max(screen_height, 1)

    def transform_point(self, cx: float, cy: float, center_x: float) -> tuple[float, float, float]:
        scale = 1.0 + cy * self.k_perspective
        if scale < 0.1:
            scale = 0.1
        sx = (cx - center_x) * scale + center_x
        sy = cy
        return sx, sy, scale

    def transform_image(self, surface: pygame.Surface, cx: float, cy: float, center_x: float) -> tuple:
        w, h = surface.get_size()
        k = self.k_perspective

        N = max(4, h // 4)
        strip_h = h / N
        strips = []

        for i in range(N):
            orig_y = i * strip_h
            orig_h = strip_h if i < N - 1 else h - orig_y

            s = 1.0 + (cy + orig_y + orig_h / 2) * k

            ix_left = math.floor((cx - center_x) * s + center_x)
            ix_right = math.floor((cx + w - center_x) * s + center_x)

            w_strip = max(1, ix_right - ix_left)
            h_strip = max(1, int(orig_h * s))

            src = pygame.Rect(0, int(orig_y), w, max(1, int(orig_h)))
            strips.append((src, w_strip, h_strip, ix_left, ix_right))

        if not strips:
            return surface, 0, 0

        min_x = min(ixl for _, _, _, ixl, _ in strips)
        max_x = max(ixr for _, _, _, _, ixr in strips)
        w_result = max(1, max_x - min_x)
        h_result = sum(hs for _, hs, _, _, _ in strips)

        s_top = 1.0 + cy * k
        sx = (cx - center_x) * s_top + center_x
        dx = min_x - int(sx)

        result = pygame.Surface((w_result, h_result), pygame.SRCALPHA)
        y_pos = 0
        for src, w_strip, h_strip, ix_left, _ in strips:
            x_in_result = ix_left - min_x
            sub = surface.subsurface(src)
            scaled = pygame.transform.scale(sub, (w_strip, h_strip))
            result.blit(scaled, (x_in_result, y_pos))
            y_pos += h_strip

        return result, dx, 0

    def inv_transform_point(self, sx: float, sy: float, center_x: float) -> tuple[float, float]:
        cy = sy
        scale = 1.0 + cy * self.k_perspective
        if abs(scale) < 0.001:
            scale = 0.001
        cx = (sx - center_x) / scale + center_x
        return cx, cy
