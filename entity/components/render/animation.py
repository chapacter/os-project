from dataclasses import dataclass

import pygame


@dataclass
class AnimationComponent:
    frames: list[pygame.Surface]
    frame_count: int
    speed: float = 1.0
    looping: bool = False
    frame_index: float = 0.0
    finished: bool = False

    @property
    def current_frame(self) -> pygame.Surface:
        idx = min(int(self.frame_index), self.frame_count - 1)
        return self.frames[idx] if self.frames else pygame.Surface((1, 1))
