from enum import Enum


class RoomTileState(Enum):
    NORMAL = "normal"
    COMBAT = "combat"


class RoomCombatState(Enum):
    ENTERING_COMBAT = "entering_combat"
    COMBAT_ACTIVE = "combat_active"
    CLEARING_COMBAT = "clearing_combat"
    RECOVERED = "recovered"
