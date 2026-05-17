from core.ecs_world import System, World
from entity.components.render.animation import AnimationComponent
from entity.components.render.render import RenderComponent


class AnimationSystem(System):
    def __init__(self, world: World):
        super().__init__(world)

    def update(self, dt: float) -> None:
        entities = self.world.query(AnimationComponent)
        for entity in entities:
            anim = self.world.get_component(entity, AnimationComponent)
            if anim.finished:
                continue

            anim.frame_index += anim.speed

            if anim.frame_index >= anim.frame_count:
                if anim.looping:
                    anim.frame_index = 0.0
                else:
                    anim.frame_index = float(anim.frame_count - 1)
                    anim.finished = True

            render = self.world.get_component(entity, RenderComponent)
            if render:
                render.image = anim.current_frame
                if hasattr(entity, "image"):
                    entity.image = render.image
