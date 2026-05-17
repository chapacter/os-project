from dataclasses import dataclass

import pygame


@dataclass
class RenderComponent:
    image: pygame.Surface
    visible: bool = True
    alpha: int = 255
