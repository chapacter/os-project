from dataclasses import dataclass


@dataclass
class TransformComponent:
    x: float = 0.0
    y: float = 0.0
    width: int = 32
    height: int = 32
    layer: int = 0

    @property
    def centerx(self) -> float:
        return self.x + self.width / 2

    @property
    def centery(self) -> float:
        return self.y + self.height / 2

    @property
    def center(self) -> tuple[float, float]:
        return (self.centerx, self.centery)

    @center.setter
    def center(self, pos: tuple[float, float]) -> None:
        self.x = pos[0] - self.width / 2
        self.y = pos[1] - self.height / 2
