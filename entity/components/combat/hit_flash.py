from dataclasses import dataclass


@dataclass
class HitFlashComponent:
    timer: int = 0
    duration: int = 2
    scale_timer: int = 0
    scale_duration: int = 4
    flash_color: tuple = (255, 255, 255, 180)
