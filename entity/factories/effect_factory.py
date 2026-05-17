import random

import pygame

from core.ecs_world import World
from entity.components.combat.damage_zone import DamageZoneComponent
from entity.components.core.lifetime import LifetimeComponent
from entity.components.core.transform import TransformComponent
from entity.components.movement.velocity import VelocityComponent
from entity.components.render.animation import AnimationComponent
from entity.components.render.render import RenderComponent
from sprites import Spritesheet
from utils.settings import GROUND_LAYER, HEALTH_LAYER, RED, SPRITE_EFFECTS


class EffectFactory:
    _preloaded_frames: dict[str, list[pygame.Surface]] = {}

    @classmethod
    def preload(cls, effects_spritesheet: Spritesheet) -> None:
        cfg = SPRITE_EFFECTS
        for effect_name, effect_info in cfg["effects"].items():
            frames = []
            frame_count = effect_info.get("frames", 1)
            for i in range(frame_count):
                frame, _ = effects_spritesheet.get_effect(effect_name, cfg, frame=i)
                frames.append(frame)
            cls._preloaded_frames[effect_name] = frames

    @classmethod
    def create_ecs_effect(cls, world: World, x: float, y: float, effect_name: str,
                          groups: list | None = None, ) -> object:
        frames = cls._preloaded_frames.get(effect_name)
        if not frames:
            return None

        cfg = SPRITE_EFFECTS["effects"].get(effect_name, {})
        frame_count = cfg.get("frames", len(frames))
        anim_speed = SPRITE_EFFECTS.get("animation_speed", 0.6)

        sprite = pygame.sprite.Sprite()
        sprite._layer = HEALTH_LAYER
        if groups:
            for g in groups:
                g.add(sprite)
        sprite.image = frames[0]
        sprite.rect = sprite.image.get_rect()
        sprite.rect.center = (x, y)

        world.add_entity(sprite)
        world.add_component(sprite, TransformComponent(x=sprite.rect.x, y=sprite.rect.y, width=sprite.rect.width,
                                                       height=sprite.rect.height, ))
        world.add_component(sprite, AnimationComponent(frames=frames, frame_count=frame_count, speed=anim_speed,
                                                       looping=False, ))
        world.add_component(sprite, RenderComponent(image=sprite.image))

        return sprite

    @classmethod
    def create_spark_particle(cls, world: World, x: float, y: float, groups: list | None = None, ) -> object:
        sprite = pygame.sprite.Sprite()
        sprite._layer = HEALTH_LAYER
        if groups:
            for g in groups:
                g.add(sprite)
        sprite.image = pygame.Surface((4, 4))
        sprite.image.fill(RED)
        sprite.rect = sprite.image.get_rect()
        sprite.rect.centerx = x + random.choice([-2, -1, 0, 1, 2])
        sprite.rect.centery = y + 2

        world.add_entity(sprite)
        world.add_component(sprite, LifetimeComponent(remaining=4))
        world.add_component(sprite, VelocityComponent(dy=1))
        world.add_component(sprite, TransformComponent(x=sprite.rect.x, y=sprite.rect.y, width=4, height=4, ))
        return sprite

    @classmethod
    def create_area_damage(cls, world: World, x: float, y: float, damage: float,
                           groups: list | None = None, ) -> object:
        sprite = pygame.sprite.Sprite()
        sprite._layer = GROUND_LAYER + 1
        if groups:
            for g in groups:
                g.add(sprite)
        sprite.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(sprite.image, (255, 50, 50, 180), (15, 15), 15)
        sprite.rect = sprite.image.get_rect()
        sprite.rect.center = (x, y)

        world.add_entity(sprite)
        world.add_component(sprite, LifetimeComponent(remaining=180))
        world.add_component(sprite, DamageZoneComponent(damage=damage, hitbox=pygame.Rect(0, 0, 30, 30), ))
        world.add_component(sprite, TransformComponent(x=sprite.rect.x, y=sprite.rect.y, width=30, height=30, ))
        return sprite

    @classmethod
    def cleanup_finished(cls, world: World) -> None:
        anim_entities = world.query(AnimationComponent)
        for entity in anim_entities:
            anim = world.get_component(entity, AnimationComponent)
            if anim and anim.finished:
                if hasattr(entity, "kill"):
                    entity.kill()
                world.remove_entity(entity)

    @classmethod
    def update(cls, world: World) -> None:
        cls.cleanup_finished(world)
