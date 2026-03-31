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
    def __init__(self, game, x, y, is_boss=False, is_elite=False, enemy_type=None):
        self.game = game
        self._layer = PLAYER_LAYER
        self.healthbar = Enemy_Healthbar(game, self, x, y)
        self.groups = game.all_sprites, game.enemies
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE

        self.is_boss = is_boss
        self.is_elite = is_elite

        if is_boss:
            self.health = ENEMY_HEALTH * 5
            self.ENEMY_SPEED_MOD = 0.5
        elif is_elite:
            self.health = ENEMY_HEALTH * 2
            self.ENEMY_SPEED_MOD = 0.8
        else:
            self.health = ENEMY_HEALTH
            self.ENEMY_SPEED_MOD = 1

        type_weights = {k: v["weight"] for k, v in ENEMY_TYPES.items()}
        self.enemy_type = (
            enemy_type if enemy_type is not None else weighted_choice(type_weights)
        )

        cfg = ENEMY_TYPES[self.enemy_type]
        self.width = cfg["sprite_size"][0]
        self.height = cfg["sprite_size"][1]

        self.velocity = pygame.math.Vector2(0, 0)

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
        self.number_steps = random.choice([30, 40, 50, 60, 70, 80, 90])
        self.stall_steps = 120
        self.current_steps = 0

        self.state = "moving"
        self.animation_counter = 0

        self.shoot_counter = 0
        self.wait_shoot = random.choice([10, 20, 30, 40, 50, 60, 70, 80, 90])
        self.shoot_state = "halt"

        self.particle_counter = 0

        Effect(self.game, self.rect.centerx, self.rect.centery, "death")

        self.physics_name = f"enemy_{id(self)}"
        if game.physics_enabled and game.physics:
            game.physics.add_entity_body(
                self.rect.x,
                self.rect.y,
                self.hitbox.width,
                self.hitbox.height,
                name=self.physics_name,
            )

    def get_direction_from_velocity(self):
        vx, vy = self.velocity.x, self.velocity.y
        if abs(vx) > abs(vy):
            return "right" if vx > 0 else "left"
        elif vy != 0:
            return "down" if vy > 0 else "up"
        return self.direction

    def shoot(self):
        self.shoot_counter += 1
        if self.shoot_counter >= self.wait_shoot:
            self.shoot_state = "shoot"
            self.shoot_counter = 0

    def move(self):
        if self.state == "moving":
            dir_map = {
                "left": pygame.math.Vector2(-1, 0),
                "right": pygame.math.Vector2(1, 0),
                "up": pygame.math.Vector2(0, -1),
                "down": pygame.math.Vector2(0, 1),
            }
            move_dir = dir_map.get(self.direction, pygame.math.Vector2(1, 0))
            speed = ENEMY_SPEED * self.ENEMY_SPEED_MOD
            self.velocity = move_dir * speed
            self.current_steps += 1

            if self.shoot_state == "shoot":
                player = self.game.player
                start_x = self.hitbox.centerx
                start_y = self.hitbox.centery
                target_x = player.hitbox.centerx
                target_y = player.hitbox.centery
                offset = 0.15
                target_x += random.randint(-50, 50) * offset
                target_y += random.randint(-50, 50) * offset
                Enemy_Bullet(
                    self.game, start_x, start_y, target_x, target_y, scatter=0.3
                )
                self.shoot_state = "halt"

            max_health = (
                ENEMY_HEALTH * 5
                if self.is_boss
                else (ENEMY_HEALTH * 2 if self.is_elite else ENEMY_HEALTH)
            )
            if self.health < max_health * 0.3:
                self.particle_counter += 1
                if self.particle_counter >= 3:
                    self.particle_counter = 0
                    Particle(self.game, self.rect.centerx, self.rect.centery)

        elif self.state == "stalling":
            self.velocity = pygame.math.Vector2(0, 0)
            self.current_steps += 1
            if self.current_steps == self.stall_steps:
                self.state = "moving"
                self.current_steps = 0
                self.direction = random.choice(["left", "right", "up", "down"])

    def animation(self):
        if self.velocity.length() == 0:
            self.image = self.animations[self.direction][0]
        else:
            frame_index = int(self.animation_counter) % self.frame_move
            self.image = self.animations[self.direction][frame_index]
            self.animation_counter += 0.2
            if self.animation_counter >= self.frame_move:
                self.animation_counter = 0

    def update(self):
        self.move()
        self.animation()
        self.rect.x += self.velocity.x
        self.rect.y += self.velocity.y
        self.hitbox.center = self.rect.center

        if self.current_steps == self.number_steps:
            if self.state != "stalling":
                self.current_steps = 0
            self.number_steps = random.choice([30, 40, 50, 60, 70, 80, 90])
            self.state = "stalling"
        self.collide_block()
        self.collide_player()
        self.shoot()

    def collide_block(self):
        for block in self.game.blocks:
            if self.hitbox.colliderect(block.rect):
                if self.direction == "left":
                    self.rect.x += ENEMY_SPEED
                    self.direction = "right"
                elif self.direction == "right":
                    self.rect.x -= ENEMY_SPEED
                    self.direction = "left"
                elif self.direction == "up":
                    self.rect.y += ENEMY_SPEED
                    self.direction = "down"
                elif self.direction == "down":
                    self.rect.y -= ENEMY_SPEED
                    self.direction = "up"
                return

    def collide_player(self):
        collide = pygame.sprite.spritecollide(self, self.game.mainPlayer, True)
        if collide:
            pass

    def damage(self, amount):
        self.health = self.health - amount
        self.healthbar.damage(ENEMY_HEALTH, self.health)
        audio_manager.play_sound("hit")

        if self.health <= 0:
            Effect(self.game, self.rect.centerx, self.rect.centery, "death")
            self.on_death()
            self.kill()
            self.healthbar.kill_bar()
            if self.game.physics and hasattr(self, "physics_name"):
                self.game.physics.remove_body(self.physics_name)

    def on_death(self):
        if not hasattr(self, "game") or not self.game:
            return

        if not hasattr(self.game, "dungeon_generator"):
            return

        tile_x = int(self.rect.x / TILESIZE)
        tile_y = int(self.rect.y / TILESIZE)

        room_tile_width = self.game.dungeon_generator.room_tile_width
        room_tile_height = self.game.dungeon_generator.room_tile_height
        wall_thickness = self.game.dungeon_generator.wall_thickness
        room_unit_width = room_tile_width + wall_thickness * 2
        room_unit_height = room_tile_height + wall_thickness * 2

        room_x = tile_x // room_unit_width
        room_y = tile_y // room_unit_height
        room_coord = (room_x, room_y)

        room = self.game.dungeon_generator.rooms.get(room_coord)
        if room and room.enemy_count > 0:
            room.enemy_count -= 1


class Enemy_Healthbar(Healthbar):
    def __init__(self, game, enemy, x, y):
        super().__init__(game, x, y, enemy)
