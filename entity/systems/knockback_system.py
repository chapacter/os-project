import pygame

from core.ecs_world import System, World
from entity.components.combat.knockback import KnockbackComponent


class KnockbackSystem(System):
    def __init__(self, world: World):
        super().__init__(world)

    def update(self, dt: float) -> None:
        for entity in self.world.query(KnockbackComponent):
            comp = self.world.get_component(entity, KnockbackComponent)
            if comp is None:
                continue
            if comp.duration_remaining > 0:
                comp.velocity *= comp.decay
                if hasattr(entity, "knockback_velocity"):
                    entity.knockback_velocity = comp.velocity
                comp.duration_remaining -= 1
                if comp.velocity.length() < 0.1:
                    comp.velocity = pygame.math.Vector2(0, 0)
                    if hasattr(entity, "knockback_velocity"):
                        entity.knockback_velocity = comp.velocity
