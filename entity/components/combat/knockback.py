from dataclasses import dataclass, field

import pygame


@dataclass
class KnockbackComponent:
    velocity: pygame.math.Vector2 = field(default_factory=lambda: pygame.math.Vector2(0, 0))
    decay: float = 0.7
    duration_remaining: int = 0
