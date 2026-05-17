from dataclasses import dataclass, field

import pygame


@dataclass
class DamageZoneComponent:
    damage: float = 0
    hitbox: pygame.Rect = field(default_factory=lambda: pygame.Rect(0, 0, 0, 0))
