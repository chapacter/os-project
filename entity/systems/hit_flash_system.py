import pygame

from core.ecs_world import System, World
from entity.components.combat.hit_flash import HitFlashComponent


class HitFlashSystem(System):
    def __init__(self, world: World):
        super().__init__(world)

    def update(self, dt: float) -> None:
        for entity in self.world.query(HitFlashComponent):
            comp = self.world.get_component(entity, HitFlashComponent)
            if comp is None:
                continue
            if comp.scale_timer > 0:
                if hasattr(entity, "image") and entity.image is not None:
                    orig_w, orig_h = entity.image.get_size()
                    entity.image = pygame.transform.scale(entity.image, (orig_w + 2, orig_h + 2))
                    if hasattr(entity, "rect") and entity.rect is not None:
                        entity.rect = entity.image.get_rect(center=entity.rect.center)
                comp.scale_timer -= 1

            if comp.timer > 0:
                if hasattr(entity, "image") and entity.image is not None:
                    mask = pygame.mask.from_surface(entity.image)
                    silhouette = mask.to_surface(setcolor=comp.flash_color, unsetcolor=(0, 0, 0, 0))
                    entity.image.blit(silhouette, (0, 0))
                comp.timer -= 1
