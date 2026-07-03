import pygame


def circle_vs_rect(cx: float, cy: float, radius: float, rect: pygame.Rect) -> bool:
    closest_x = max(rect.left, min(cx, rect.right))
    closest_y = max(rect.top, min(cy, rect.bottom))
    dx = cx - closest_x
    dy = cy - closest_y
    return dx * dx + dy * dy < radius * radius
