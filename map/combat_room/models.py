from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import pygame

from map.combat_room.enums import RoomTileState, RoomCombatState


@dataclass
class RoomTileData:
    sprite: pygame.sprite.Sprite
    tile_x: int
    tile_y: int
    state: RoomTileState = RoomTileState.NORMAL
    original_image: Optional[pygame.Surface] = None
    combat_image: Optional[pygame.Surface] = None
    flash_counter: int = 0
    _flash_target: str = ""
    edge_mask: dict = field(default_factory=dict)


@dataclass
class RoomTransitionData:
    room_coord: tuple[int, int]
    state: RoomCombatState = RoomCombatState.ENTERING_COMBAT
    tiles: list[RoomTileData] = field(default_factory=list)
    propagator: Any = None
