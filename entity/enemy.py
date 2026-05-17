import random

import pygame

from entity.base import Healthbar, VectorEntity
from entity.factories.effect_factory import EffectFactory
from projectiles.bullet import Enemy_Bullet
from utils import weighted_choice
from utils.physics import COLLISION_ENTITY
from utils.settings import *


class Enemy(VectorEntity, pygame.sprite.Sprite):
    def __init__(self, game, x, y, enemy_type=None, hp_multiplier=1.0):
        self.game = game
        self._layer = PLAYER_LAYER
        self.groups = game.all_sprites, game.enemies
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE

        type_weights = {k: v["weight"] for k, v in ENEMY_TYPES.items()}
        self.enemy_type = (
            enemy_type if enemy_type is not None else weighted_choice(type_weights)
        )

        cfg = ENEMY_TYPES[self.enemy_type]
        self.width = cfg["sprite_size"][0]
        self.height = cfg["sprite_size"][1]

        self.speed_mod = cfg["speed_mod"]
        self.detection_range = cfg["detection_range"]
        self.attack_range = cfg["attack_range"]
        self.retreat_range = cfg["retreat_range"]
        self.retreat_distance = cfg["retreat_distance"]
        self.melee_range = cfg["melee_range"]
        self.attack_damage = cfg["damage"]
        self.shoot_cooldown = cfg["shoot_cooldown"]
        self.melee_cooldown = cfg["melee_cooldown"]
        self.always_chase = cfg["always_chase"]
        self.has_blink = cfg["has_blink"]
        self.blink_interval = cfg.get("blink_interval", 8)

        self.healthbar = Enemy_Healthbar(game, self, x, y)

        self.frame_move = cfg.get("frame_move", 3)
        self.animations = {}
        direction_map = cfg.get("direction_map", {"down": 0, "left": 1, "right": 2, "up": 3})

        spritesheet = game.enemy_spritesheets[self.enemy_type]
        sprite_w, sprite_h = cfg["sprite_size"]

        for direction, row in direction_map.items():
            frames = []
            for col in range(self.frame_move):
                sprite = spritesheet.get_image(
                    col * sprite_w, row * sprite_h, self.width, self.height
                )
                frames.append(sprite)
            self.animations[direction] = frames

        self.image = self.animations["down"][0]
        self.rect = self.image.get_rect()
        self.rect.x = self.x
        self.rect.y = self.y

        self.hitbox = pygame.Rect(0, 0, HITBOX_WIDTH, HITBOX_HEIGHT)
        self.hitbox.center = self.rect.center

        self.direction = random.choice(["left", "right", "up", "down"])
        self.ai_state = "patrol"
        self.has_seen_player = False
        self.animation_counter = 0

        self.shoot_counter = 0
        self.shoot_state = "halt"
        self.melee_timer = 0

        self.retreat_progress = 0
        self.wait_after_retreat = 0

        self.blink_timer = 0
        self.visible = True

        # Float position accumulators — fix sub-pixel truncation
        self._pos_x = float(self.hitbox.x)
        self._pos_y = float(self.hitbox.y)

        # Patrol improvements
        self.patrol_timer = 0
        self.patrol_target_x = 0
        self.patrol_target_y = 0

        # Retreat vector cache
        self._retreat_vector = pygame.math.Vector2(0, 0)

        # Spawn effect
        EffectFactory.create_ecs_effect(self.game.ecs_world, self.rect.centerx, self.rect.centery, "death",
                                        groups=[self.game.all_sprites], )

        tile_x = int(self.rect.x / TILESIZE)
        tile_y = int(self.rect.y / TILESIZE)
        room_tile_width = self.game.dungeon_generator.room_tile_width
        room_tile_height = self.game.dungeon_generator.room_tile_height
        wall_thickness = self.game.dungeon_generator.wall_thickness
        room_unit_width = room_tile_width + wall_thickness * 2
        room_unit_height = room_tile_height + wall_thickness * 2
        self.home_room = (tile_x // room_unit_width, tile_y // room_unit_height)
        self._set_patrol_target()

        self.physics_name = f"enemy_{id(self)}"
        VectorEntity.__init__(self, game, self.physics_name, collision_type=COLLISION_ENTITY, max_health=int(cfg["hp"] * hp_multiplier))

        # Replace default pymunk body with one sized to hitbox
        if self.body:
            game.physics.remove_body(self.physics_name)
        self.body, self.shape = game.physics.add_entity_body(
            self.rect.x,
            self.rect.y,
            self.hitbox.width,
            self.hitbox.height,
            name=self.physics_name,
        )

    # ─── AI Helpers ───────────────────────────────────────────────

    def _get_distance_to_player(self):
        if not self.game.player:
            return float("inf")
        dx = self.game.player.rect.centerx - self.rect.centerx
        dy = self.game.player.rect.centery - self.rect.centery
        return (dx ** 2 + dy ** 2) ** 0.5

    def _get_direction_to_player(self):
        if not self.game.player:
            return self.direction
        dx = self.game.player.rect.centerx - self.rect.centerx
        dy = self.game.player.rect.centery - self.rect.centery
        if abs(dx) > abs(dy):
            return "right" if dx > 0 else "left"
        return "down" if dy > 0 else "up"

    def _is_player_in_melee_range(self):
        return self._get_distance_to_player() <= self.melee_range

    def _set_patrol_target(self):
        hx, hy = self.home_room
        room_tile_width = self.game.dungeon_generator.room_tile_width
        room_tile_height = self.game.dungeon_generator.room_tile_height
        wall_thickness = self.game.dungeon_generator.wall_thickness
        room_unit_width = room_tile_width + wall_thickness * 2
        room_unit_height = room_tile_height + wall_thickness * 2

        margin = 2
        tx = random.randint(
            hx * room_unit_width + wall_thickness + margin,
            hx * room_unit_width + wall_thickness + room_tile_width - margin,
        )
        ty = random.randint(
            hy * room_unit_height + wall_thickness + margin,
            hy * room_unit_height + wall_thickness + room_tile_height - margin,
        )
        self.patrol_target_x = tx * TILESIZE
        self.patrol_target_y = ty * TILESIZE
        self.patrol_timer = random.randint(120, 360)

    # ─── AI States ────────────────────────────────────────────────

    def _patrol(self):
        self.patrol_timer -= 1
        if self.patrol_timer <= 0:
            self._set_patrol_target()

        dx = self.patrol_target_x - self.rect.centerx
        dy = self.patrol_target_y - self.rect.centery
        vec = pygame.math.Vector2(dx, dy)
        if vec.length() > 0:
            vec = vec.normalize()
        speed = ENEMY_SPEED * self.speed_mod
        self.velocity = vec * speed
        self.direction = self.get_direction_from_velocity()

    def _retreat(self):
        if self.retreat_progress == 0:
            dx = self.rect.centerx - self.game.player.rect.centerx
            dy = self.rect.centery - self.game.player.rect.centery
            vec = pygame.math.Vector2(dx, dy)
            if vec.length() > 0:
                vec = vec.normalize()
            self._retreat_vector = vec
            self.retreat_progress = 1

        speed = ENEMY_SPEED * self.speed_mod
        self.velocity = self._retreat_vector * speed
        self.direction = self.get_direction_from_velocity()
        self.retreat_progress += speed

        if self.retreat_progress >= self.retreat_distance:
            self.velocity = pygame.math.Vector2(0, 0)
            self.retreat_progress = 0
            self.wait_after_retreat = 0

    def _wait(self):
        self.velocity = pygame.math.Vector2(0, 0)
        self.wait_after_retreat -= 1
        if self.wait_after_retreat <= 0:
            self.wait_after_retreat = 0

    def _chase(self):
        if not self.game.player:
            return
        dx = self.game.player.rect.centerx - self.rect.centerx
        dy = self.game.player.rect.centery - self.rect.centery
        vec = pygame.math.Vector2(dx, dy)
        if vec.length() > 0:
            vec = vec.normalize()
        speed = ENEMY_SPEED * self.speed_mod
        self.velocity = vec * speed
        self.direction = self.get_direction_from_velocity()

    def _ranged_attack(self):
        self.direction = self._get_direction_to_player()
        self.velocity = pygame.math.Vector2(0, 0)

        if self.shoot_state == "shoot":
            player = self.game.player
            start_x = self.hitbox.centerx
            start_y = self.hitbox.centery
            if ENEMY_TYPES[self.enemy_type].get("cone_attack"):
                import math
                cone_spread = 0.2
                target_x = player.hitbox.centerx
                target_y = player.hitbox.centery
                angle = math.atan2(target_y - start_y, target_x - start_x)
                for i in range(-1, 2):
                    a = angle + i * cone_spread
                    ex = start_x + math.cos(a) * 100
                    ey = start_y + math.sin(a) * 100
                    Enemy_Bullet(self.game, start_x, start_y, ex, ey)
            else:
                target_x = player.hitbox.centerx + random.randint(-15, 15)
                target_y = player.hitbox.centery + random.randint(-15, 15)
                Enemy_Bullet(self.game, start_x, start_y, target_x, target_y)
            self.shoot_state = "halt"

    def _melee_attack(self):
        if not self.game.player:
            return
        dx = self.game.player.rect.centerx - self.rect.centerx
        dy = self.game.player.rect.centery - self.rect.centery
        vec = pygame.math.Vector2(dx, dy)
        if vec.length() > 0:
            vec = vec.normalize()
        speed = ENEMY_SPEED * self.speed_mod * 0.5
        self.velocity = vec * speed
        self.direction = self.get_direction_from_velocity()

        self.melee_timer += 1
        if self.melee_timer >= self.melee_cooldown:
            if self._is_player_in_melee_range():
                self.game.player.damage(self.attack_damage)
            self.melee_timer = 0

    def _handle_blink(self):
        self.blink_timer += 1
        if self.blink_timer >= self.blink_interval:
            self.blink_timer = 0
            self.visible = not self.visible
            if self.visible:
                self.image.set_alpha(255)
            else:
                self.image.set_alpha(0)

    # ─── Core ─────────────────────────────────────────────────────

    def shoot(self):
        if self.shoot_state == "shoot":
            return
        self.shoot_counter += 1
        if self.shoot_counter >= self.shoot_cooldown:
            self.shoot_state = "shoot"
            self.shoot_counter = 0

    def _avoid_other_enemies(self):
        SEPARATION_RADIUS = 80
        SEPARATION_FORCE = 5.0

        if not hasattr(self.game, 'enemies'):
            return

        avoidance = pygame.math.Vector2(0, 0)
        for other in self.game.enemies:
            if other is self:
                continue
            dx = self.rect.centerx - other.rect.centerx
            dy = self.rect.centery - other.rect.centery
            dist = (dx ** 2 + dy ** 2) ** 0.5

            if 0 < dist < SEPARATION_RADIUS:
                force = (SEPARATION_RADIUS - dist) / SEPARATION_RADIUS * SEPARATION_FORCE
                if dist > 0:
                    avoidance += pygame.math.Vector2(dx, dy).normalize() * force

        self.velocity += avoidance

    def move(self):
        if self.enemy_type in [5, 6, 7]:
            self._avoid_other_enemies()

        distance = self._get_distance_to_player()

        if distance <= self.detection_range:
            self.has_seen_player = True

        if not self.has_seen_player:
            state = "patrol"
        elif (
                self.retreat_range > 0
                and distance <= self.retreat_range
                and self.retreat_progress == 0
        ):
            state = "retreat"
        elif self.retreat_progress > 0:
            state = "retreat"
        elif self.wait_after_retreat > 0:
            state = "wait"
        elif distance <= self.melee_range:
            state = "melee"
        elif distance <= self.attack_range and self.shoot_cooldown > 0:
            state = "ranged"
        else:
            state = "chase"

        if state == "patrol":
            self._patrol()
        elif state == "retreat":
            self._retreat()
        elif state == "wait":
            self._wait()
        elif state == "chase":
            self._chase()
        elif state == "ranged":
            self._ranged_attack()
        elif state == "melee":
            self._melee_attack()

        if self.has_blink:
            if state in ["patrol", "chase"] and self.velocity.length() > 0:
                self._handle_blink()
            elif state in ["ranged", "melee"]:
                if not self.visible:
                    self.visible = True
                    self.image.set_alpha(255)

    def animation(self):
        if self.has_blink and not self.visible:
            return

        anim_dir = (
            self.get_direction_from_velocity()
            if self.velocity.length() > 0
            else self.direction
        )

        if self.velocity.length() == 0:
            self.image = self.animations[anim_dir][0]
        else:
            frame_index = int(self.animation_counter) % self.frame_move
            self.image = self.animations[anim_dir][frame_index]
            self.animation_counter += 0.2
            if self.animation_counter >= self.frame_move:
                self.animation_counter = 0

        if self.has_blink:
            self.image.set_alpha(255 if self.visible else 0)

    def apply_movement(self):
        # Knockback — float-accumulated
        if self.knockback_velocity.length() > 0:
            self._pos_x += self.knockback_velocity.x
            self.hitbox.x = int(self._pos_x)
            self._resolve_collision_x("knockback_velocity")
            self._pos_y += self.knockback_velocity.y
            self.hitbox.y = int(self._pos_y)
            self._resolve_collision_y("knockback_velocity")
            self.knockback_velocity *= ENEMY_KNOCKBACK_DECAY
            if self.knockback_velocity.length() < 0.1:
                self.knockback_velocity = pygame.math.Vector2(0, 0)

        # Velocity — float-accumulated (fixes sub-pixel truncation)
        self._pos_x += self.velocity.x
        self.hitbox.x = int(self._pos_x)
        self._resolve_collision_x("velocity")
        self._pos_y += self.velocity.y
        self.hitbox.y = int(self._pos_y)
        self._resolve_collision_y("velocity")

        self.rect.center = self.hitbox.center
        self.sync_physics()

    def update(self):
        self.move()
        self.animation()

        self.apply_hit_effect()

        self.apply_movement()

        # Home room management
        if not self._is_inside_home_room():
            self._snap_to_home_room()

        self.collide_player()
        self.shoot()

    # ─── Combat ───────────────────────────────────────────────────

    def collide_player(self):
        collide = pygame.sprite.spritecollide(self, self.game.mainPlayer, False)
        if collide:
            pass

    def damage(self, amount):
        super().damage(amount)
        self.healthbar.damage(self.max_health, self.health)

    def _on_death(self):
        EffectFactory.create_ecs_effect(self.game.ecs_world, self.rect.centerx, self.rect.centery, "death",
                                        groups=[self.game.all_sprites], )
        self.healthbar.kill_bar()
        self.kill()
        if self.game.physics and hasattr(self, "physics_name"):
            self.game.physics.remove_body(self.physics_name)

        if hasattr(self.game, "dungeon_generator"):
            room_coord = self._get_current_room_coord()
            room = self.game.dungeon_generator.rooms.get(room_coord)
            if room and room.enemy_count > 0:
                room.enemy_count -= 1

    # ─── Room ─────────────────────────────────────────────────────

    def _get_current_room_coord(self):
        tile_x = int(self.rect.x / TILESIZE)
        tile_y = int(self.rect.y / TILESIZE)
        room_tile_width = self.game.dungeon_generator.room_tile_width
        room_tile_height = self.game.dungeon_generator.room_tile_height
        wall_thickness = self.game.dungeon_generator.wall_thickness
        room_unit_width = room_tile_width + wall_thickness * 2
        room_unit_height = room_tile_height + wall_thickness * 2
        return (tile_x // room_unit_width, tile_y // room_unit_height)

    def _is_inside_home_room(self):
        current_room = self._get_current_room_coord()
        return current_room == self.home_room

    def _snap_to_home_room(self):
        hx, hy = self.home_room
        room_tile_width = self.game.dungeon_generator.room_tile_width
        room_tile_height = self.game.dungeon_generator.room_tile_height
        wall_thickness = self.game.dungeon_generator.wall_thickness
        room_unit_width = room_tile_width + wall_thickness * 2
        room_unit_height = room_tile_height + wall_thickness * 2

        center_x = hx * room_unit_width + wall_thickness + room_tile_width // 2
        center_y = hy * room_unit_height + wall_thickness + room_tile_height // 2
        self.rect.x = center_x * TILESIZE - self.width // 2
        self.rect.y = center_y * TILESIZE - self.height // 2
        self.velocity = pygame.math.Vector2(0, 0)
        self.has_seen_player = False
        self.retreat_progress = 0
        self.wait_after_retreat = 0
        self._set_patrol_target()


class Enemy_Healthbar(Healthbar):
    def __init__(self, game, enemy, x, y):
        super().__init__(game, x, y, enemy)
