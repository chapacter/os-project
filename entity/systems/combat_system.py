from core.ecs_world import System, World
from entity.components.combat.health import HealthComponent


class CombatSystem(System):
    def __init__(self, world: World):
        super().__init__(world)

    def update(self, dt: float) -> None:
        for entity in self.world.query(HealthComponent):
            comp = self.world.get_component(entity, HealthComponent)
            if comp is None:
                continue
            if comp.died and hasattr(entity, "_on_death"):
                comp.died = False
                entity._on_death()
