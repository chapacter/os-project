from __future__ import annotations

from typing import Callable

from core.ecs_world import System
from map.combat_room.enums import RoomCombatState, RoomTileState


class CombatRoomTransitionSystem(System):
    def __init__(self, world, get_dm: Callable):
        super().__init__(world)
        self._get_dm = get_dm

    def update(self, dt: float) -> None:
        dm = self._get_dm()
        if dm is None:
            return
        transitions = dm.get_active_transitions()
        for coord, tr in list(transitions.items()):
            if tr.state == RoomCombatState.ENTERING_COMBAT:
                self._process_forward(tr, dt)
            elif tr.state == RoomCombatState.CLEARING_COMBAT:
                self._process_reverse(tr, coord, dt, dm)

    def _process_forward(self, tr, dt: float) -> None:
        reached = tr.propagator.advance(dt)
        for tile in reached:
            if tile.combat_image is not None:
                tile.sprite.image = tile.combat_image
            tile.state = RoomTileState.COMBAT
        if tr.propagator.is_complete:
            tr.state = RoomCombatState.COMBAT_ACTIVE

    def _process_reverse(self, tr, coord, dt: float, dm) -> None:
        cleared = tr.propagator.retract(dt)
        for tile in cleared:
            if tile.original_image is not None:
                tile.sprite.image = tile.original_image
            tile.state = RoomTileState.NORMAL
        if tr.propagator.is_retracted:
            tr.state = RoomCombatState.RECOVERED
            dm._open_room_doors(coord)
            dm.game._sealed_rooms.pop(coord, None)
            dm._room_transitions.pop(coord, None)
