import random

import pygame

from effects.effect import Effect
from effects.particle import Particle
from entity.base import Healthbar
from projectiles.bullet import Enemy_Bullet
from utils import weighted_choice
from utils.audio import audio_manager
from utils.settings import *


class Enemy(pygame.sprite.Sprite):
    def __init__(self, game, x, y, enemy_type=None):
        self.game = game
        self._layer = PLAYER_LAYER
        self.groups = game.all_sprites, game.enemies
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE

        type_weights = {k: v["weight"] for k, v in ENEMY_TYPES.items()}
        self.enemy_type = enemy_type if enemy_type is not None else weighted_choice(type_weights)

        cfg = ENEMY_TYPES[self.enemy_type]
        self.width = cfg["sprite_size"][0]
        self.height = cfg["sprite_size"][1]

        self.max_health = cfg["hp"]
        self.health = self.max_health
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

        self.velocity = pygame.math.Vector2(0, 0)
        self.knockback_velocity = pygame.math.Vector2(0, 0)

        self.hit_flash_timer = 0
        self.hit_flash_duration = 2

        self.body = None
        self.shape = None

        self.frame_move = 3
        self.animations = {}
        direction_map = {"down": 0, "left": 1, "right": 2, "up": 3}

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

        self.particle_counter = 0

        Effect(self.game, self.rect.centerx, self.rect.centery, "death")

        tile_x = int(self.rect.x / TILESIZE)
        tile_y = int(self.rect.y / TILESIZE)
        room_tile_width = self.game.dungeon_generator.room_tile_width
        room_tile_height = self.game.dungeon_generator.room_tile_height
        wall_thickness = self.game.dungeon_generator.wall_thickness
        room_unit_width = room_tile_width + wall_thickness * 2
        room_unit_height = room_tile_height + wall_thickness * 2
        self.home_room = (tile_x // room_unit_width, tile_y // room_unit_height)

        self.physics_name = f"enemy_{id(self)}"
        if game.physics_enabled and game.physics:
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

    def _dir_to_vec(self, direction):
        return {
            "left": pygame.math.Vector2(-1, 0),
            "right": pygame.math.Vector2(1, 0),
            "up": pygame.math.Vector2(0, -1),
            "down": pygame.math.Vector2(0, 1),
        }.get(direction, pygame.math.Vector2(1, 0))

    def _is_player_in_melee_range(self):
        return self._get_distance_to_player() <= self.melee_range

    def _get_free_directions(self):
        free_dirs = []
        test_dist = ENEMY_SPEED * 3
        for direction in ["left", "right", "up", "down"]:
            test_rect = pygame.Rect(self.hitbox)
            if direction == "left":
                test_rect.x -= test_dist
            elif direction == "right":
                test_rect.x += test_dist
            elif direction == "up":
                test_rect.y -= test_dist
            elif direction == "down":
                test_rect.y += test_dist

            blocked = False
            for block in self.game.blocks:
                if test_rect.colliderect(block.rect):
                    blocked = True
                    break
            if not blocked:
                free_dirs.append(direction)
        return free_dirs

    # ─── AI States ────────────────────────────────────────────────

    def _patrol(self):
        dir_map = {
            "left": pygame.math.Vector2(-1, 0),
            "right": pygame.math.Vector2(1, 0),
            "up": pygame.math.Vector2(0, -1),
            "down": pygame.math.Vector2(0, 1),
        }
        move_dir = dir_map.get(self.direction, pygame.math.Vector2(1, 0))
        speed = ENEMY_SPEED * self.speed_mod
        self.velocity = move_dir * speed

    def _retreat(self):
        if self.retreat_progress == 0:
            direction = self._get_direction_to_player()
            opposite = {"left": "right", "right": "left", "up": "down", "down": "up"}
            self.direction = opposite[direction]
            self.retreat_progress = 1

        speed = ENEMY_SPEED * self.speed_mod
        self.velocity = self._dir_to_vec(self.direction) * speed
        self.retreat_progress += speed

        if self.retreat_progress >= self.retreat_distance:
            self.velocity = pygame.math.Vector2(0, 0)
            self.retreat_progress = 0
            self.wait_after_retreat = 30

    def _wait(self):
        self.velocity = pygame.math.Vector2(0, 0)
        self.wait_after_retreat -= 1
        if self.wait_after_retreat <= 0:
            self.wait_after_retreat = 0

    def _chase(self):
        direction = self._get_direction_to_player()
        self.direction = direction
        speed = ENEMY_SPEED * self.speed_mod
        self.velocity = self._dir_to_vec(direction) * speed

    def _ranged_attack(self):
        self.direction = self._get_direction_to_player()
        self.velocity = pygame.math.Vector2(0, 0)

        if self.shoot_state == "shoot":
            player = self.game.player
            start_x = self.hitbox.centerx
            start_y = self.hitbox.centery
            target_x = player.hitbox.centerx + random.randint(-15, 15)
            target_y = player.hitbox.centery + random.randint(-15, 15)
            Enemy_Bullet(self.game, start_x, start_y, target_x, target_y)
            self.shoot_state = "halt"

    def _melee_attack(self):
        self.direction = self._get_direction_to_player()
        speed = ENEMY_SPEED * self.speed_mod * 0.5
        self.velocity = self._dir_to_vec(self.direction) * speed

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

    def move(self):
        distance = self._get_distance_to_player()

        if distance <= self.detection_range:
            self.has_seen_player = True

        if not self.has_seen_player:
            state = "patrol"
        elif self.retreat_range > 0 and distance <= self.retreat_range and self.retreat_progress == 0:
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

        if self.health < self.max_health * 0.3:
            self.particle_counter += 1
            if self.particle_counter >= 3:
                self.particle_counter = 0
                Particle(self.game, self.rect.centerx, self.rect.centery)

    def animation(self):
        if self.has_blink and not self.visible:
            return

        if self.velocity.length() == 0:
            self.image = self.animations[self.direction][0]
        else:
            frame_index = int(self.animation_counter) % self.frame_move
            self.image = self.animations[self.direction][frame_index]
            self.animation_counter += 0.2
            if self.animation_counter >= self.frame_move:
                self.animation_counter = 0

        if self.has_blink:
            self.image.set_alpha(255 if self.visible else 0)

    def update(self):
        self.move()
        self.animation()

        # Hit flash (mask-based white silhouette)
        if self.hit_flash_timer > 0:
            mask = pygame.mask.from_surface(self.image)
            white_silhouette = mask.to_surface(
                setcolor=(255, 255, 255, 180), unsetcolor=(0, 0, 0, 0)
            )
            self.image.blit(white_silhouette, (0, 0))
            self.hit_flash_timer -= 1

        # Knockback decay + axis-separated collision
        if self.knockback_velocity.length() > 0:
            self.hitbox.x += self.knockback_velocity.x
            self._resolve_collision_x("knockback_velocity")
            self.hitbox.y += self.knockback_velocity.y
            self._resolve_collision_y("knockback_velocity")
            self.knockback_velocity *= ENEMY_KNOCKBACK_DECAY
            if self.knockback_velocity.length() < 0.1:
                self.knockback_velocity = pygame.math.Vector2(0, 0)

        # Velocity axis-separated collision
        self.hitbox.x += self.velocity.x
        self._resolve_collision_x("velocity")
        self.hitbox.y += self.velocity.y
        self._resolve_collision_y("velocity")

        self.rect.center = self.hitbox.center
        self.sync_physics()

        # Home room management
        if not self._is_inside_home_room():
            self._snap_to_home_room()

        self.collide_player()
        self.shoot()

    # ─── Physics ──────────────────────────────────────────────────

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

    def sync_physics(self):
        if self.body:
            self.game.physics.set_body_velocity(self.physics_name, self.velocity)
            self.game.physics.sync_entity_to_body(self.physics_name, self.rect)

    # ─── Combat ───────────────────────────────────────────────────

    def take_knockback(self, direction, force):
        self.knockback_velocity = direction * force
        self.hit_flash_timer = self.hit_flash_duration

    def collide_player(self):
        collide = pygame.sprite.spritecollide(self, self.game.mainPlayer, False)
        if collide:
            pass

    def damage(self, amount):
        self.health -= amount
        self.healthbar.damage(self.max_health, self.health)
        audio_manager.play_sound("hit")

        if self.health <= 0:
            self._on_death()

    def _on_death(self):
        Effect(self.game, self.rect.centerx, self.rect.centery, "death")
        self.kill()
        self.healthbar.kill_bar()
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


class Enemy_Healthbar(Healthbar):
    def __init__(self, game, enemy, x, y):
        super().__init__(game, x, y, enemy)
