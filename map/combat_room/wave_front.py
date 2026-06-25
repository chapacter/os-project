from __future__ import annotations

import random
from collections import defaultdict

from map.combat_room.models import RoomTileData


class WaveFront:
    def __init__(
            self,
            tiles: list[RoomTileData],
            origin_x: int,
            origin_y: int,
            tiles_per_second: float = 120,
    ):
        groups = defaultdict(list)
        for tile in tiles:
            d = abs(tile.tile_x - origin_x) + abs(tile.tile_y - origin_y)
            groups[d // 3].append(tile)

        self._sorted = []
        for d in sorted(groups.keys()):
            random.shuffle(groups[d])
            self._sorted.extend(groups[d])
        self._tps = tiles_per_second
        self._accumulator = 0.0
        self._forward_idx = 0
        self._retract_idx = -1

    def advance(self, dt: float) -> list[RoomTileData]:
        if self._forward_idx >= len(self._sorted):
            return []
        self._accumulator += self._tps * dt
        count = int(self._accumulator)
        if count == 0:
            return []
        self._accumulator -= count
        old_idx = self._forward_idx
        self._forward_idx = min(self._forward_idx + count, len(self._sorted))
        return self._sorted[old_idx:self._forward_idx]

    @property
    def is_complete(self) -> bool:
        return self._forward_idx >= len(self._sorted)

    def start_retract(self) -> None:
        self._retract_idx = self._forward_idx
        self._accumulator = 0.0

    def retract(self, dt: float) -> list[RoomTileData]:
        if self._retract_idx <= 0:
            return []
        self._accumulator += self._tps * dt
        count = int(self._accumulator)
        if count == 0:
            return []
        self._accumulator -= count
        old_idx = self._retract_idx
        self._retract_idx = max(self._retract_idx - count, 0)
        return self._sorted[self._retract_idx:old_idx]

    @property
    def is_retracted(self) -> bool:
        if self._retract_idx < 0:
            return False
        return self._retract_idx <= 0
