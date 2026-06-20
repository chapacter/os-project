from dataclasses import dataclass

import pygame


@dataclass
class BlockColliderComponent:
    hitbox: pygame.Rect
    noclip: bool = False
    use_float_pos: bool = False
    pos_x: float = 0.0
    pos_y: float = 0.0
