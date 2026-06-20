from typing import Any

from entity.components.core.transform import TransformComponent
from entity.components.render.render import RenderComponent


def ecs_register(
        world: Any,
        entity: Any,
        *,
        rect: Any = None,
        layer: int = 0,
        image: Any = None,
) -> None:
    if not world:
        return

    if not world.has_entity(entity):
        world.add_entity(entity)

    if rect:
        world.add_component(
            entity,
            TransformComponent(
                x=rect.x,
                y=rect.y,
                width=rect.width,
                height=rect.height,
                layer=layer,
            ),
        )

    if image:
        world.add_component(entity, RenderComponent(image=image))


def ecs_unregister(world: Any, entity: Any) -> None:
    if world and world.has_entity(entity):
        world.remove_entity(entity)


def ecs_sync_from_rect(entity: Any) -> None:
    if not hasattr(entity, "rect") or not entity.rect:
        return
    rect = entity.rect
    tc = getattr(entity, "transform_comp", None)
    if tc is not None:
        tc.x = rect.x
        tc.y = rect.y
        tc.width = rect.width
        tc.height = rect.height


def ecs_sync_to_rect(entity: Any) -> None:
    tc = getattr(entity, "transform_comp", None)
    if tc is not None and hasattr(entity, "rect") and entity.rect is not None:
        entity.rect.x = int(tc.x)
        entity.rect.y = int(tc.y)
        entity.rect.width = tc.width
        entity.rect.height = tc.height
