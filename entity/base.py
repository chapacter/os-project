import pygame

from entity.components.collision.block_collider import BlockColliderComponent
from entity.components.combat.health import HealthComponent
from entity.components.combat.hit_flash import HitFlashComponent
from entity.components.combat.knockback import KnockbackComponent
from entity.factories.effect_factory import EffectFactory
from utils.settings import *


class VectorEntity:
    def __init__(self, game, physics_name=None, collision_type=None, create_body=True, max_health=None):
        self.game = game
        self.velocity = pygame.math.Vector2(0, 0)
        self.direction = "right"
        self.physics_name = physics_name
        self.body = None
        self.shape = None

        mh = max_health if max_health is not None else 5
        self.health_comp = HealthComponent(health=mh, max_health=mh)
        self.hit_flash_comp = HitFlashComponent()
        self.knockback_comp = KnockbackComponent()
        hitbox = self.hitbox if hasattr(self, "hitbox") else pygame.Rect(0, 0, HITBOX_WIDTH, HITBOX_HEIGHT)
        self.block_collider_comp = BlockColliderComponent(hitbox=hitbox)

        if hasattr(self, "game") and self.game and hasattr(self.game, "ecs_world") and self.game.ecs_world:
            w = self.game.ecs_world
            if not w.has_entity(self):
                w.add_entity(self)
            w.add_component(self, self.health_comp)
            w.add_component(self, self.hit_flash_comp)
            w.add_component(self, self.knockback_comp)
            w.add_component(self, self.block_collider_comp)

        if hasattr(self, "_pos_x"):
            self.block_collider_comp.pos_x = self._pos_x
            self.block_collider_comp.pos_y = self._pos_y
            self.block_collider_comp.use_float_pos = True

        self.particle_counter = 0

        if create_body and game.physics_enabled and game.physics:
            self.body, self.shape = game.physics.add_entity_body(0, 0, HITBOX_WIDTH, HITBOX_HEIGHT,
                                                                 name=self.physics_name,
                                                                 collision_type=collision_type, )

    def get_direction_from_velocity(self):
        vx, vy = self.velocity.x, self.velocity.y
        if abs(vx) > abs(vy):
            return "right" if vx > 0 else "left"
        elif vy != 0:
            return "down" if vy > 0 else "up"
        return self.direction

    def sync_physics(self):
        if self.body:
            self.game.physics.set_body_velocity(self.physics_name, self.velocity)
            self.game.physics.sync_entity_to_body(self.physics_name, self.rect)

    def apply_hit_effect(self, flash_color=(255, 255, 255, 180)):
        hf = self.hit_flash_comp
        if hf.scale_timer > 0:
            orig_w, orig_h = self.image.get_size()
            self.image = pygame.transform.scale(self.image, (orig_w + 2, orig_h + 2))
            self.rect = self.image.get_rect(center=self.rect.center)
            hf.scale_timer -= 1

        if hf.timer > 0:
            mask = pygame.mask.from_surface(self.image)
            silhouette = mask.to_surface(setcolor=flash_color, unsetcolor=(0, 0, 0, 0))
            self.image.blit(silhouette, (0, 0))
            hf.timer -= 1

        if self.health_comp.health < self.health_comp.max_health * 0.3:
            self.particle_counter += 1
            if self.particle_counter >= 3:
                self.particle_counter = 0
                EffectFactory.create_spark_particle(self.game.ecs_world, self.rect.centerx, self.rect.centery,
                                                    groups=[self.game.all_sprites], )

    def take_knockback(self, direction, force):
        kb = self.knockback_comp
        kb.velocity = direction * force
        hf = self.hit_flash_comp
        hf.timer = hf.duration
        hf.scale_timer = hf.scale_duration
        kb.duration_remaining = 10

    def damage(self, amount):
        hp = self.health_comp
        hp.health -= amount
        self.game.services.audio.play_sound("hit")
        hf = self.hit_flash_comp
        hf.timer = hf.duration
        hf.scale_timer = hf.scale_duration
        if hp.health <= 0:
            hp.died = True

    def _on_death(self):
        pass


class Entity(VectorEntity, pygame.sprite.Sprite):
    def __init__(self, game, x, y, layer, groups, physics_name="entity", collision_type=None):
        self._layer = layer
        self.groups = groups
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE
        self.width = TILESIZE
        self.height = TILESIZE

        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self.hitbox = pygame.Rect(0, 0, HITBOX_WIDTH, HITBOX_HEIGHT)
        self.hitbox.center = self.rect.center

        VectorEntity.__init__(self, game, physics_name, collision_type)

    def update_hitbox(self):
        self.hitbox.center = self.rect.center


class Healthbar(pygame.sprite.Sprite):
    def __init__(self, game, x, y, entity=None):
        self.game = game
        self._layer = HEALTH_LAYER
        self.groups = game.all_sprites, game.healthbar
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE
        self.width = 30
        self.height = 10

        self.image = pygame.Surface([self.width, self.height])
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y - TILESIZE / 2

        self.entity = entity

    def move(self):
        self.rect.x = self.entity.rect.x
        self.rect.y = self.entity.rect.y - TILESIZE / 2

    def damage(self, total_health, health):
        self.image.fill(RED)
        width = self.rect.width * health / total_health
        pygame.draw.rect(self.image, GREEN, (0, 0, width, self.height), 0)

    def kill_bar(self):
        self.kill()

    def update(self):
        self.move()
