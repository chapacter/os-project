from core.ecs_world import System, World
from entity.components.core.lifetime import LifetimeComponent


class LifetimeSystem(System):
    def __init__(self, world: World):
        super().__init__(world)

    def update(self, dt: float) -> None:
        to_remove = []
        for entity in self.world.query(LifetimeComponent):
            comp = self.world.get_component(entity, LifetimeComponent)
            if comp is None:
                continue
            comp.remaining -= 1
            if comp.remaining <= 0:
                to_remove.append(entity)
        for entity in to_remove:
            if hasattr(entity, "kill"):
                entity.kill()
            self.world.remove_entity(entity)
