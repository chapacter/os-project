import pygame

from effects.effect import Effect
from effects.particle import Particle
from entity.base import Healthbar
from projectiles.bullet import Bullet
from settings import *


class Player(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        self.game = game
        self._layer = PLAYER_LAYER
        self.healthbar = Player_Healthbar(game, self, x, y)

        self.groups = game.all_sprites, game.mainPlayer
        pygame.sprite.Sprite.__init__(self, self.groups)

        self.x = x * TILESIZE
        self.y = y * TILESIZE

        self.sprite_cfg = SPRITE_PLAYER
        self.width = self.sprite_cfg["target_size"][0]
        self.height = self.sprite_cfg["target_size"][1]
        self.offset_x = self.sprite_cfg["offset"][0]
        self.offset_y = self.sprite_cfg["offset"][1]

        self.x_change = 0
        self.y_change = 0
        self.frame_move = 6
        self.frame_attack = 4
        self.frame_dodge = 5

        # Предзагрузка анимаций
        self.animations = {}
        direction_map = {"right": 0, "up": 1, "down": 2, "left": 3}
        animation_offsets = {"move": 0, "attack": 6, "dodge": 10}

        # Анимация движения (6 кадров)
        self.animations["move"] = {}
        for direction, row in direction_map.items():
            frames = []
            for col in range(self.frame_move):
                sprite, _ = game.player_spritesheet.get_image_centered(
                    animation_offsets["move"] + col, row, self.sprite_cfg
                )
                frames.append(sprite)
            self.animations["move"][direction] = frames

        # Анимация атаки (4 кадра)
        self.animations["attack"] = {}
        for direction, row in direction_map.items():
            frames = []
            for col in range(self.frame_attack):
                sprite, _ = game.player_spritesheet.get_image_centered(
                    animation_offsets["attack"] + col, row, self.sprite_cfg
                )
                frames.append(sprite)
            self.animations["attack"][direction] = frames

        # Анимация переката (5 кадров)
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

    def move(self):
        pressed = pygame.key.get_pressed()

        if (
                pressed[pygame.K_SPACE]
                and not self.is_dodging
                and self.dodge_state == "ready"
        ):
            self.dodge_roll()

        if self.is_dodging:
            if self.direction == "left":
                self.x_change -= PLAYER_SPEED
            elif self.direction == "right":
                self.x_change += PLAYER_SPEED
            elif self.direction == "up":
                self.y_change -= PLAYER_SPEED
            elif self.direction == "down":
                self.y_change += PLAYER_SPEED
        else:
            if pressed[pygame.K_a] or pressed[pygame.K_LEFT]:
                self.x_change -= PLAYER_SPEED
                self.direction = "left"
            elif pressed[pygame.K_d] or pressed[pygame.K_RIGHT]:
                self.x_change += PLAYER_SPEED
                self.direction = "right"
            if pressed[pygame.K_w] or pressed[pygame.K_UP]:
                self.y_change -= PLAYER_SPEED
                self.direction = "up"
            elif pressed[pygame.K_s] or pressed[pygame.K_DOWN]:
                self.y_change += PLAYER_SPEED
                self.direction = "down"

        if self.x_change != 0 or self.y_change != 0:
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
        self.rect.x = self.rect.x + self.x_change
        self.rect.y = self.rect.y + self.y_change
        self.hitbox.center = self.rect.center

        self.collide_block()
        self.collide_enemy()
        self.collide_weapon()
        self.attack()
        self.dodge_cooldown_update()
        self.wait_after_shoot()
        self.x_change = 0
        self.y_change = 0

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

        else:  # move
            if self.x_change == 0 and self.y_change == 0:
                self.image = self.animations["move"][self.direction][0]
            else:
                frame_index = int(self.action_frame) % self.frame_move
                self.image = self.animations["move"][self.direction][frame_index]
                self.action_frame += 0.8
                if self.action_frame >= self.frame_move:
                    self.action_frame = 0

    def collide_block(self):
        pressed = pygame.key.get_pressed()
        collide = False
        for block in self.game.blocks:
            if self.hitbox.colliderect(block.rect):
                collide = True
                break

        if collide:
            self.game.block_collided = True
            if pressed[pygame.K_a]:
                self.rect.x += PLAYER_SPEED
            elif pressed[pygame.K_d]:
                self.rect.x -= PLAYER_SPEED
            if pressed[pygame.K_w]:
                self.rect.y += PLAYER_SPEED
            elif pressed[pygame.K_s]:
                self.rect.y -= PLAYER_SPEED
        else:
            self.game.block_collided = False

    def collide_enemy(self):
        pressed = pygame.key.get_pressed()
        collide = False
        for enemy in self.game.enemies:
            if self.hitbox.colliderect(enemy.rect):
                collide = True
                break

        if collide:
            self.game.enemy_collided = True
            if pressed[pygame.K_a]:
                self.rect.x += PLAYER_SPEED
            elif pressed[pygame.K_d]:
                self.rect.x -= PLAYER_SPEED
            elif pressed[pygame.K_w]:
                self.rect.y += PLAYER_SPEED
            elif pressed[pygame.K_s]:
                self.rect.y -= PLAYER_SPEED
        else:
            self.game.enemy_collided = False

    def collide_weapon(self):
        collide = pygame.sprite.spritecollide(self, self.game.weapons, True)
        if collide:
            self.sword_equipped = True

    def attack(self):
        pressed = pygame.key.get_pressed()
        if self.shoot_state == "shoot":
            if self.sword_equipped:
                if pressed[pygame.K_j]:
                    Bullet(self.game, self.rect.x, self.rect.y)
                    self.action_state = "attack"
                    self.action_frame = 0
                    self.shoot_state = "wait"

    def dodge_roll(self):
        self.is_dodging = True
        self.action_state = "dodge"
        self.action_frame = 0
        self.dodge_state = "cooldown"
        self.dodge_cooldown_counter = -20

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
        self.healthbar.damage(PLAYER_HEALTH, self.health)

        if self.health <= 0:
            self.kill()
            self.healthbar.kill_bar()


class Player_Healthbar(Healthbar):
    def __init__(self, game, player, x, y):
        super().__init__(game, x, y, player)
