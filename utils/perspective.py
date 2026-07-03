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
        sy = cy * scale
        return sx, sy, scale

    def transform_image(self, surface: pygame.Surface, cx: float, cy: float, center_x: float) -> tuple:
        w, h = surface.get_size()
        k = self.k_perspective
        s_top = 1.0 + cy * k

        N = max(4, h // 4)
        strip_h = h / N
        strips = []
        y_acc = 0.0

        for i in range(N):
            orig_y = i * strip_h
            orig_h = strip_h if i < N - 1 else h - orig_y

            strip_cy = cy + orig_y + orig_h / 2
            s = 1.0 + strip_cy * k

            w_strip = max(1, int(w * s))
            h_strip = max(1, int(orig_h * s))

            src = pygame.Rect(0, int(orig_y), w, max(1, int(orig_h)))
            sub = surface.subsurface(src)
            scaled = pygame.transform.scale(sub, (w_strip, h_strip))

            left_off = (cx - center_x) * (s - s_top)
            strips.append((scaled, left_off, y_acc))
            y_acc += h_strip

        if not strips:
            return surface, 0, 0

        h_result = int(y_acc)
        min_x = min(off for _, off, _ in strips)
        max_x = max(off + s.get_width() for s, off, _ in strips)
        w_result = max(1, int(max_x - min_x))

        result = pygame.Surface((w_result, h_result), pygame.SRCALPHA)
        for scaled, left_off, y_pos in strips:
            result.blit(scaled, (int(left_off - min_x), int(y_pos)))

        return result, int(min_x), 0

    def inv_transform_point(self, sx: float, sy: float, center_x: float) -> tuple[float, float]:
        k = self.k_perspective
        if abs(k) < 1e-10:
            cy = sy
        else:
            disc = 1.0 + 4.0 * k * sy
            if disc < 0.0:
                disc = 0.0
            cy = (-1.0 + math.sqrt(disc)) / (2.0 * k)
        scale = 1.0 + cy * k
        if abs(scale) < 0.001:
            scale = 0.001
        cx = (sx - center_x) / scale + center_x
        return cx, cy
