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
        scale = 1.0 + cy * self.k_perspective
        if scale < 0.1:
            scale = 0.1

        sx_left = int((cx - center_x) * scale + center_x)
        sx_right = int((cx + w - center_x) * scale + center_x)
        w_result = max(1, sx_right - sx_left)

        h_result = max(1, int(h * scale))

        result = pygame.transform.scale(surface, (w_result, h_result))
        return result, 0, 0

    def inv_transform_point(self, sx: float, sy: float, center_x: float) -> tuple[float, float]:
        cy = sy
        scale = 1.0 + cy * self.k_perspective
        if abs(scale) < 0.001:
            scale = 0.001
        cx = (sx - center_x) / scale + center_x
        return cx, cy
