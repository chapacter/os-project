from collections.abc import Callable

from core.ecs_world import System, World
from entity.components.combat.damage_zone import DamageZoneComponent


class AreaDamageSystem(System):
    def __init__(self, world: World, get_player_fn: Callable):
        super().__init__(world)
        self.get_player = get_player_fn

    def update(self, dt: float) -> None:
        player = self.get_player()
        if not player:
            return
        if not hasattr(player, "hitbox"):
            return
        for entity in self.world.query(DamageZoneComponent):
            zone = self.world.get_component(entity, DamageZoneComponent)
            if zone is None:
                continue
            zone.hitbox.center = entity.rect.center if hasattr(entity, "rect") else (0, 0)
            if zone.hitbox.colliderect(player.hitbox):
                player.damage(zone.damage)
