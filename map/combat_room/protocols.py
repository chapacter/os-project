from __future__ import annotations

from typing import Protocol

from map.combat_room.models import RoomTileData


class WavePropagator(Protocol):
    def advance(self, dt: float) -> list[RoomTileData]:
        ...

    @property
    def is_complete(self) -> bool:
        ...

    def start_retract(self) -> None:
        ...

    def retract(self, dt: float) -> list[RoomTileData]:
        ...

    @property
    def is_retracted(self) -> bool:
        ...
