import math
from abc import ABC, abstractmethod


class PerspectiveConfig:
    def __init__(self, angle_deg: float = 15.0):
        self.angle_deg = angle_deg
        self.shear_tan = math.tan(math.radians(angle_deg))


class PerspectiveTransformStrategy(ABC):
    @abstractmethod
    def transform_point(self, cx: float, cy: float, center_x: float) -> tuple[float, float, float]:
        ...

    @abstractmethod
    def get_quad_corners(self, cx: float, cy: float, w: float, h: float, center_x: float) -> list | None:
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
        self.world_anchor_delta = 0.0

    def _anchor_cy(self, cy):
        return cy + self.world_anchor_delta

    def _screen_y(self, cy):
        wad = self.world_anchor_delta
        k = self.k_perspective
        return cy * (1.0 + k * wad) + k * cy * cy / 2.0

    def transform_point(self, cx: float, cy: float, center_x: float) -> tuple[float, float, float]:
        k = self.k_perspective
        wad = self.world_anchor_delta
        horizon = -(1.0 / k + wad) if k > 0 else float('-inf')
        if cy < horizon:
            cy = horizon
        scale = 1.0 + (cy + wad) * k
        if scale < 0.1:
            scale = 0.1
        sx = (cx - center_x) * scale + center_x
        sy = self._screen_y(cy)
        return sx, sy, scale

    def get_quad_corners(self, cx: float, cy: float, w: float, h: float, center_x: float) -> list | None:
        k = self.k_perspective
        wad = self.world_anchor_delta
        horizon = -(1.0 / k + wad) if k > 0 else float('-inf')
        if cy + h <= horizon:
            return None

        cy_top = cy if cy >= horizon else horizon
        cy_bot = max(cy + h, cy_top + 1)

        s_top = 1.0 + (cy_top + wad) * k
        s_bot = 1.0 + (cy_bot + wad) * k
        if s_top < 0.1:
            s_top = 0.1
        if s_bot < 0.1:
            s_bot = 0.1

        xl_top = (cx - center_x) * s_top + center_x
        xr_top = (cx + w - center_x) * s_top + center_x
        xl_bot = (cx - center_x) * s_bot + center_x
        xr_bot = (cx + w - center_x) * s_bot + center_x

        sy_top = self._screen_y(cy_top)
        sy_bot = self._screen_y(cy_bot)

        sw = self.screen_width
        sh = self.screen_height
        if not any(0 <= x < sw and 0 <= y < sh for x, y in
                   [(xl_top, sy_top), (xr_top, sy_top), (xr_bot, sy_bot), (xl_bot, sy_bot)]):
            return None

        return [(int(xl_top), int(sy_top)),
                (int(xr_top), int(sy_top)),
                (int(xr_bot), int(sy_bot)),
                (int(xl_bot), int(sy_bot))]

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
