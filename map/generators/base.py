from typing import Protocol


class MapGeneratorStrategy(Protocol):
    def generate(self, floor_number: int = 1) -> list[list[str]]:
        ...

    def get_start_position(self) -> tuple[int, int]:
        ...

    @property
    def map_width(self) -> int:
        ...

    @property
    def map_height(self) -> int:
        ...

    @property
    def rooms(self) -> dict:
        ...
