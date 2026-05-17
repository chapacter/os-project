from core.ecs_world import System, World
from core.event_bus import EventBus
from core.events import ENEMY_KILLED, PLAYER_DIED
from entity.components.combat.health import HealthComponent


class CombatSystem(System):
    def __init__(self, world: World):
        super().__init__(world)
        self.bus = world.get(EventBus)

    def update(self, dt: float) -> None:
        for entity in self.world.query(HealthComponent):
            comp = self.world.get_component(entity, HealthComponent)
            if comp is None:
                continue
            if comp.died:
                comp.died = False
                if hasattr(entity, "_on_death"):
                    entity._on_death()
                if hasattr(entity, "_get_current_room_coord"):
                    self.bus.emit(ENEMY_KILLED, entity=entity)
                else:
                    self.bus.emit(PLAYER_DIED, entity=entity)
