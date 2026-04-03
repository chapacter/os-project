import math

import pygame

from effects.effect import Effect
from effects.particle import Particle
from entity.base import VectorEntity
from projectiles.bullet import Bullet
from utils.audio import audio_manager
from utils.settings import *


class Player(VectorEntity, pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = PLAYER_LAYER

        self.groups = game.all_sprites, game.mainPlayer
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE

        self.sprite_cfg = SPRITE_PLAYER
        self.width = self.sprite_cfg["target_size"][0]
        self.height = self.sprite_cfg["target_size"][1]
        self.offset_x = self.sprite_cfg["offset"][0]
        self.offset_y = self.sprite_cfg["offset"][1]

        self.frame_move = 6
        self.frame_attack = 4
        self.frame_dodge = 5

        self.animations = {}
        direction_map = {"right": 0, "up": 1, "down": 2, "left": 3}
        animation_offsets = {"move": 0, "attack": 6, "dodge": 10}

        self.animations["move"] = {}
        for direction, row in direction_map.items():
            frames = []
            for col in range(self.frame_move):
                sprite, _ = game.player_spritesheet.get_image_centered(
                    animation_offsets["move"] + col, row, self.sprite_cfg
                )
                frames.append(sprite)
            self.animations["move"][direction] = frames

        self.animations["attack"] = {}
        for direction, row in direction_map.items():
            frames = []
            for col in range(self.frame_attack):
                sprite, _ = game.player_spritesheet.get_image_centered(
                    animation_offsets["attack"] + col, row, self.sprite_cfg
                )
                frames.append(sprite)
            self.animations["attack"][direction] = frames

        self.animations["dodge"] = {}
        for direction, row in direction_map.items():
            frames = []
            for col in range(self.frame_dodge):
                sprite, _ = game.player_spritesheet.get_image_centered(
                    animation_offsets["dodge"] + col, row, self.sprite_cfg
                )
                frames.append(sprite)
            self.animations["dodge"][direction] = frames

        self.image = self.animations["move"]["right"][0]
        self.rect = self.image.get_rect()
        self.rect.center = (self.x + self.offset_x, self.y + self.offset_y)

        self.hitbox = pygame.Rect(0, 0, HITBOX_WIDTH, HITBOX_HEIGHT)
        self.hitbox.center = self.rect.center

        VectorEntity.__init__(self, game, "player", 4)

        self.sword_equipped = True

        self.counter = 0
        self.wait_time = 10
        self.shoot_state = "shoot"

        self.grass_counter = 0
        self.particle_counter = 0

        self.action_state = "move"
        self.action_frame = 0
        self.attack_direction = "right"
        self.is_dodging = False
        self.dodge_frames = self.frame_dodge
        self.dodge_state = "ready"
        self.dodge_cooldown = 4
        self.dodge_cooldown_counter = 0

        self.health = PLAYER_HEALTH

        self.is_input_active = False

        self.knockback_duration_remaining = 0
        self.contact_knockback_cooldown = 0

    def move(self):
        pressed = pygame.key.get_pressed()

        if (
                pressed[pygame.K_SPACE]
                and not self.is_dodging
                and self.dodge_state == "ready"
        ):
            self.dodge_roll()

        if self.is_dodging:
            if self.dodge_velocity and self.dodge_velocity.length() > 0:
                self.dodge_velocity *= 0.92
                self.velocity = self.dodge_velocity
            else:
                self.velocity = pygame.math.Vector2(0, 0)
        else:
            input_vec = pygame.math.Vector2(0, 0)
            if pressed[pygame.K_a] or pressed[pygame.K_LEFT]:
                input_vec.x -= 1
                self.direction = "left"
            if pressed[pygame.K_d] or pressed[pygame.K_RIGHT]:
                input_vec.x += 1
                self.direction = "right"
            if pressed[pygame.K_w] or pressed[pygame.K_UP]:
                input_vec.y -= 1
                self.direction = "up"
            if pressed[pygame.K_s] or pressed[pygame.K_DOWN]:
                input_vec.y += 1
                self.direction = "down"

            if input_vec.length() > 0:
                input_vec = input_vec.normalize()
                self.velocity = input_vec * PLAYER_SPEED
                self.direction = self.get_direction_from_velocity()
                self.is_input_active = True
            else:
                self.velocity *= 0.80
                self.is_input_active = False
                if self.velocity.length() < 0.2:
                    self.velocity = pygame.math.Vector2(0, 0)

        if self.velocity.length() > 0:
            self.grass_counter += 1
            if self.grass_counter >= 5:
                self.grass_counter = 0
                Effect(self.game, self.rect.centerx, self.rect.bottom, "grass")

            if self.health < PLAYER_HEALTH * 0.3:
                self.particle_counter += 1
                if self.particle_counter >= 3:
                    self.particle_counter = 0
                    Particle(self.game, self.rect.centerx, self.rect.centery)

    def update(self):
        self.move()
        self.animation()

        if self.knockback_duration_remaining > 0:
            self.knockback_velocity *= KNOCKBACK_DECAY
            self.knockback_duration_remaining -= 1
            if self.knockback_velocity.length() < 0.1:
                self.knockback_velocity = pygame.math.Vector2(0, 0)

        if self.contact_knockback_cooldown > 0:
            self.contact_knockback_cooldown -= 1

        self.apply_movement()

        self.collide_enemy()
        self.collide_weapon()
        self.attack()
        self.dodge_cooldown_update()
        self.wait_after_shoot()

    def animation(self):
        if self.action_state == "attack":
            frame_index = int(self.action_frame)
            if frame_index >= len(self.animations["attack"][self.attack_direction]):
                frame_index = len(self.animations["attack"][self.attack_direction]) - 1
            self.image = self.animations["attack"][self.attack_direction][frame_index]
            self.action_frame += 0.375
            if self.action_frame >= self.frame_attack:
                self.action_state = "move"
                self.action_frame = 0

        elif self.action_state == "dodge":
            frame_index = int(self.action_frame)
            if frame_index >= len(self.animations["dodge"][self.direction]):
                frame_index = len(self.animations["dodge"][self.direction]) - 1
            self.image = self.animations["dodge"][self.direction][frame_index]
            self.action_frame += 0.5
            if self.action_frame >= self.dodge_frames:
                self.is_dodging = False
                self.action_state = "move"
                self.action_frame = 0

        elif self.knockback_duration_remaining > 0:
            total = len(self.animations["dodge"][self.direction])
            frame = max(0, total - 1 - int(self.action_frame))
            frame = min(frame, total - 1)
            self.image = self.animations["dodge"][self.direction][frame]
            self.action_frame += 0.5

        else:
            if self.is_input_active and self.velocity.length() > 0:
                frame_index = int(self.action_frame) % self.frame_move
                self.image = self.animations["move"][self.direction][frame_index]
                self.action_frame += 0.8
                if self.action_frame >= self.frame_move:
                    self.action_frame = 0
            else:
                self.image = self.animations["move"][self.direction][0]

    def collide_enemy(self):
        MAX_PUSH = 3
        for enemy in self.game.enemies:
            if self.hitbox.colliderect(enemy.hitbox):
                self.game.enemy_collided = True

                if self.contact_knockback_cooldown <= 0:
                    contact_dir = pygame.math.Vector2(
                        self.rect.centerx - enemy.rect.centerx,
                        self.rect.centery - enemy.rect.centery,
                    )
                    if contact_dir.length() > 0:
                        contact_dir = contact_dir.normalize()
                    self.knockback_velocity = (
                            contact_dir * CONTACT_KNOCKBACK_FORCE * 0.7
                            + self.velocity * 0.3
                    )
                    self.knockback_duration_remaining = KNOCKBACK_DURATION
                    self.contact_knockback_cooldown = CONTACT_KNOCKBACK_INTERVAL

                overlap_x = min(
                    self.rect.right - enemy.rect.left,
                    enemy.rect.right - self.rect.left,
                )
                overlap_y = min(
                    self.rect.bottom - enemy.rect.top,
                    enemy.rect.bottom - self.rect.top,
                )
                if overlap_x < overlap_y:
                    push = min(overlap_x, MAX_PUSH)
                    if self.rect.centerx < enemy.rect.centerx:
                        self.rect.x -= push
                    else:
                        self.rect.x += push
                else:
                    push = min(overlap_y, MAX_PUSH)
                    if self.rect.centery < enemy.rect.centery:
                        self.rect.y -= push
                    else:
                        self.rect.y += push
                return
        self.game.enemy_collided = False

    def collide_weapon(self):
        collide = pygame.sprite.spritecollide(self, self.game.weapons, True)
        if collide:
            self.sword_equipped = True

    def attack(self):
        if self.shoot_state != "shoot":
            return
        if not self.sword_equipped:
            return

        pressed_keys = pygame.key.get_pressed()
        pressed_mouse = pygame.mouse.get_pressed()

        if pressed_keys[pygame.K_j]:
            self._attack_direction()
        elif pressed_mouse[0]:
            self._attack_cursor()

    def _attack_direction(self):
        start_x = self.hitbox.centerx
        start_y = self.hitbox.centery

        if self.velocity.length() > 0:
            attack_dir = self.velocity.normalize() * 100
        else:
            dir_map = {
                "right": (100, 0),
                "left": (-100, 0),
                "up": (0, 100),
                "down": (0, -100),
            }
            attack_dir = pygame.math.Vector2(*dir_map.get(self.direction, (100, 0)))

        if abs(attack_dir.x) > abs(attack_dir.y):
            self.attack_direction = "right" if attack_dir.x > 0 else "left"
        else:
            self.attack_direction = "down" if attack_dir.y > 0 else "up"

        force = SWORD_KNOCKBACK_FORCE if self.sword_equipped else BULLET_KNOCKBACK_FORCE
        Bullet(
            self.game,
            start_x,
            start_y,
            start_x + attack_dir.x,
            start_y + attack_dir.y,
            knockback_force=force,
        )
        self._finish_attack()

    def _attack_cursor(self):
        mouse_world = self.game.camera.to_world(pygame.mouse.get_pos())

        dx = mouse_world[0] - self.hitbox.centerx
        dy = mouse_world[1] - self.hitbox.centery
        if abs(dx) > abs(dy):
            self.attack_direction = "right" if dx > 0 else "left"
        else:
            self.attack_direction = "down" if dy > 0 else "up"

        force = SWORD_KNOCKBACK_FORCE if self.sword_equipped else BULLET_KNOCKBACK_FORCE
        Bullet(
            self.game,
            self.hitbox.centerx,
            self.hitbox.centery,
            mouse_world[0],
            mouse_world[1],
            knockback_force=force,
        )
        self._finish_attack()

    def _finish_attack(self):
        self.action_state = "attack"
        self.action_frame = 0
        self.shoot_state = "wait"
        audio_manager.play_sound("swipe")

    def dodge_roll(self):
        self.is_dodging = True
        self.action_state = "dodge"
        self.action_frame = 0
        self.dodge_state = "cooldown"
        self.dodge_cooldown_counter = -20
        dodge_speed = PLAYER_SPEED * 2.0
        if self.velocity.length() > 0:
            self.dodge_velocity = self.velocity.normalize() * dodge_speed
        else:
            dir_map = {
                "left": pygame.math.Vector2(-1, 0),
                "right": pygame.math.Vector2(1, 0),
                "up": pygame.math.Vector2(0, -1),
                "down": pygame.math.Vector2(0, 1),
            }
            self.dodge_velocity = (
                    dir_map.get(self.direction, pygame.math.Vector2(1, 0)) * dodge_speed
            )
        audio_manager.play_sound("evade")

    def dodge_cooldown_update(self):
        if self.dodge_state == "cooldown":
            self.dodge_cooldown_counter += 1
            if self.dodge_cooldown_counter >= self.dodge_cooldown:
                self.dodge_state = "ready"
                self.dodge_cooldown_counter = 0

    def wait_after_shoot(self):
        if self.shoot_state == "wait":
            self.counter += 1
            if self.counter >= self.wait_time:
                self.counter = 0
                self.shoot_state = "shoot"

    def damage(self, amount):
        self.health = self.health - amount
        audio_manager.play_sound("hit")

        if self.health <= 0:
            self.kill()

    def interact(self):
        closest = None
        closest_dist = TILESIZE * 1.5
        for obj in self.game.interactables:
            dist = math.hypot(
                obj.rect.centerx - self.rect.centerx,
                obj.rect.centery - self.rect.centery,
            )
            if dist < closest_dist:
                closest_dist = dist
                closest = obj
        if closest:
            closest.interact()
