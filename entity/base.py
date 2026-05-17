import pygame

from entity.factories.effect_factory import EffectFactory
from utils.audio import audio_manager
from utils.settings import *


class VectorEntity:
    def __init__(self, game, physics_name=None, collision_type=None, create_body=True, max_health=None):
        self.game = game
        self.velocity = pygame.math.Vector2(0, 0)
        self.knockback_velocity = pygame.math.Vector2(0, 0)
        self.direction = "right"
        self.physics_name = physics_name
        self.body = None
        self.shape = None

        self.max_health = max_health if max_health is not None else 5
        self.health = self.max_health

        self.hit_flash_timer = 0
        self.hit_flash_duration = 2
        self.hit_scale_timer = 0
        self.hit_scale_duration = self.hit_flash_duration + 2

        self.knockback_duration_remaining = 0

        self.particle_counter = 0

        if create_body and game.physics_enabled and game.physics:
            self.body, self.shape = game.physics.add_entity_body(
                0,
                0,
                HITBOX_WIDTH,
                HITBOX_HEIGHT,
                name=self.physics_name,
                collision_type=collision_type,
            )

    def get_direction_from_velocity(self):
        vx, vy = self.velocity.x, self.velocity.y
        if abs(vx) > abs(vy):
            return "right" if vx > 0 else "left"
        elif vy != 0:
            return "down" if vy > 0 else "up"
        return self.direction

    def _resolve_collision_x(self, velocity_attr="velocity"):
        vel = getattr(self, velocity_attr)
        if vel.x == 0:
            return False
        for block in self.game.blocks:
            if self.hitbox.colliderect(block.rect):
                if vel.x > 0:
                    self.hitbox.right = block.rect.left
                else:
                    self.hitbox.left = block.rect.right
                vel.x = 0
                return True
        return False

    def _resolve_collision_y(self, velocity_attr="velocity"):
        vel = getattr(self, velocity_attr)
        if vel.y == 0:
            return False
        for block in self.game.blocks:
            if self.hitbox.colliderect(block.rect):
                if vel.y > 0:
                    self.hitbox.bottom = block.rect.top
                else:
                    self.hitbox.top = block.rect.bottom
                vel.y = 0
                return True
        return False

    def apply_movement(self):
        self.hitbox.x += self.knockback_velocity.x
        self._resolve_collision_x("knockback_velocity")
        self.hitbox.y += self.knockback_velocity.y
        self._resolve_collision_y("knockback_velocity")

        self.hitbox.x += self.velocity.x
        self._resolve_collision_x("velocity")
        self.hitbox.y += self.velocity.y
        self._resolve_collision_y("velocity")

        self.rect.center = self.hitbox.center
        self.sync_physics()

    def sync_physics(self):
        if self.body:
            self.game.physics.set_body_velocity(self.physics_name, self.velocity)
            self.game.physics.sync_entity_to_body(self.physics_name, self.rect)

    def decay_knockback(self, decay_factor):
        if self.knockback_velocity.length() > 0:
            self.knockback_velocity *= decay_factor
            if self.knockback_velocity.length() < 0.1:
                self.knockback_velocity = pygame.math.Vector2(0, 0)

    def apply_hit_effect(self, flash_color=(255, 255, 255, 180)):
        if self.hit_scale_timer > 0:
            orig_w, orig_h = self.image.get_size()
            self.image = pygame.transform.scale(self.image, (orig_w + 2, orig_h + 2))
            self.rect = self.image.get_rect(center=self.rect.center)
            self.hit_scale_timer -= 1

        if self.hit_flash_timer > 0:
            mask = pygame.mask.from_surface(self.image)
            silhouette = mask.to_surface(setcolor=flash_color, unsetcolor=(0, 0, 0, 0))
            self.image.blit(silhouette, (0, 0))
            self.hit_flash_timer -= 1

        if self.health < self.max_health * 0.3:
            self.particle_counter += 1
            if self.particle_counter >= 3:
                self.particle_counter = 0
                EffectFactory.create_spark_particle(self.game.ecs_world, self.rect.centerx, self.rect.centery,
                                                    groups=[self.game.all_sprites], )

    def take_knockback(self, direction, force):
        self.knockback_velocity = direction * force
        self.hit_flash_timer = self.hit_flash_duration
        self.hit_scale_timer = self.hit_scale_duration
        self.knockback_duration_remaining = 10

    def damage(self, amount):
        self.health -= amount
        audio_manager.play_sound("hit")
        self.hit_flash_timer = self.hit_flash_duration
        self.hit_scale_timer = self.hit_scale_duration
        if self.health <= 0:
            self._on_death()

    def _on_death(self):
        pass


class Entity(VectorEntity, pygame.sprite.Sprite):
    def __init__(
            self, game, x, y, layer, groups, physics_name="entity", collision_type=None
    ):
        self._layer = layer
        self.groups = groups
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE
        self.width = TILESIZE
        self.height = TILESIZE

        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

        VectorEntity.__init__(self, game, physics_name, collision_type)

        self.hitbox = pygame.Rect(0, 0, HITBOX_WIDTH, HITBOX_HEIGHT)
        self.hitbox.center = self.rect.center

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
