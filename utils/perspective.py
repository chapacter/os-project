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
    def transform_image(self, surface: pygame.Surface, scale: float) -> pygame.Surface:
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

    def transform_image(self, surface: pygame.Surface, scale: float) -> pygame.Surface:
        if abs(scale - 1.0) < 0.001:
            return surface
        new_w = max(1, int(surface.get_width() * scale))
        new_h = max(1, int(surface.get_height() * scale))
        return pygame.transform.scale(surface, (new_w, new_h))

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
