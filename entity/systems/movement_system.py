from core.ecs_world import System, World
from entity.components.core.transform import TransformComponent
from entity.components.movement.velocity import VelocityComponent


class MovementSystem(System):
    def __init__(self, world: World):
        super().__init__(world)

    def update(self, dt: float) -> None:
        for entity in self.world.query(TransformComponent, VelocityComponent):
            tf = self.world.get_component(entity, TransformComponent)
            vel = self.world.get_component(entity, VelocityComponent)
            if tf is None or vel is None:
                continue
            tf.x += vel.dx
            tf.y += vel.dy
            if hasattr(entity, "rect") and entity.rect is not None:
                entity.rect.x = int(tf.x)
                entity.rect.y = int(tf.y)
