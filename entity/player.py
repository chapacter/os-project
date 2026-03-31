import pygame

from effects.effect import Effect
from effects.particle import Particle
from projectiles.bullet import Bullet
from utils.audio import audio_manager
from utils.settings import *


class Player(pygame.sprite.Sprite):
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

        self.velocity = pygame.math.Vector2(0, 0)
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

        self.direction = "right"
        self.sword_equipped = True

        self.counter = 0
        self.wait_time = 10
        self.shoot_state = "shoot"

        self.grass_counter = 0
        self.particle_counter = 0

        self.action_state = "move"
        self.action_frame = 0
        self.is_dodging = False
        self.dodge_frames = self.frame_dodge
        self.dodge_state = "ready"
        self.dodge_cooldown = 4
        self.dodge_cooldown_counter = 0

        self.health = PLAYER_HEALTH

        self.physics_name = "player"
        self.is_input_active = False

        if game.physics_enabled and game.physics:
            from utils.physics import COLLISION_PLAYER

            game.physics.add_entity_body(
                self.rect.x,
                self.rect.y,
                self.hitbox.width,
                self.hitbox.height,
                name=self.physics_name,
                collision_type=COLLISION_PLAYER,
            )

    def get_direction_from_velocity(self):
        vx, vy = self.velocity.x, self.velocity.y
        if abs(vx) > abs(vy):
            return "right" if vx > 0 else "left"
        elif vy != 0:
            return "down" if vy > 0 else "up"
        return self.direction

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

        self.hitbox.x += self.velocity.x
        for block in self.game.blocks:
            if self.hitbox.colliderect(block.rect):
                self.game.block_collided = True
                if self.velocity.x > 0:
                    self.hitbox.right = block.rect.left
                else:
                    self.hitbox.left = block.rect.right
                self.velocity.x = 0
                break
        else:
            self.game.block_collided = False

        self.hitbox.y += self.velocity.y
        for block in self.game.blocks:
            if self.hitbox.colliderect(block.rect):
                if self.velocity.y > 0:
                    self.hitbox.bottom = block.rect.top
                else:
                    self.hitbox.top = block.rect.bottom
                self.velocity.y = 0
                break

        self.rect.center = self.hitbox.center

        self.collide_enemy()
        self.collide_weapon()
        self.attack()
        self.dodge_cooldown_update()
        self.wait_after_shoot()

    def animation(self):
        if self.action_state == "attack":
            frame_index = int(self.action_frame)
            if frame_index >= len(self.animations["attack"][self.direction]):
                frame_index = len(self.animations["attack"][self.direction]) - 1
            self.image = self.animations["attack"][self.direction][frame_index]
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
            if self.hitbox.colliderect(enemy.rect):
                self.game.enemy_collided = True
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

        direction_offsets = {
            "right": (100, 0),
            "left": (-100, 0),
            "up": (0, 100),
            "down": (0, -100),
        }
        offset = direction_offsets.get(self.direction, (100, 0))

        Bullet(self.game, start_x, start_y, start_x + offset[0], start_y + offset[1])
        self._finish_attack()

    def _attack_cursor(self):
        mouse_world = self.game.camera.to_world(pygame.mouse.get_pos())

        Bullet(
            self.game,
            self.hitbox.centerx,
            self.hitbox.centery,
            mouse_world[0],
            mouse_world[1],
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
        print(f"[DEBUG] Player damaged, health: {self.health}")
        audio_manager.play_sound("hit")

        if self.health <= 0:
            self.kill()
